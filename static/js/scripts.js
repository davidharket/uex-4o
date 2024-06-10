$(document).ready(function() {
    let initialSequenceDone = false;
    let chatOpened = false;
    let isSendingMessage = false;

    function startShake() {
        $('#open-chat').css('animation', 'shake 0.5s');
        setTimeout(function() {
            $('#open-chat').css('animation', 'none');
        }, 500);
    }

    let shakeInterval = setInterval(function() {
        if (!chatOpened) {
            startShake();
        }
    }, 5000);

    function checkInitialMessageStatus() {
        $.get('/initial_message_status', function(response) {
            initialSequenceDone = response.initial_message_shown;
            if (initialSequenceDone) {
                loadChatHistory(); // Load chat history if initial message was already shown
            }
        });
    }

    function loadChatHistory() {
        $.get('/get_chat_history', function(chatHistory) {
            $('#messages-container').empty(); // Clear the container to avoid duplication
            chatHistory.forEach(function(message) {
                if (message.role === 'assistant' && message.buttons) {
                    displayMessage(message.content, message.role);
                    displayButtons(message.buttons);
                } else {
                    displayMessage(message.content, message.role);
                }
            });
            scrollToBottom(); // Ensure scroll to bottom after loading chat history
        });
    }

    $('#open-chat').click(function() {
        if (!$('#chat-container').hasClass('active')) {
            $('#chat-container').addClass('active');
            chatOpened = true;
            clearInterval(shakeInterval);
            if (!initialSequenceDone) {
                $.post('/set_initial_message_shown', function() {
                    displayInitialMessage();
                });
            } else {
                loadChatHistory(); // Load chat history if initial message was already shown
            }
        } else {
            $('#chat-container').removeClass('active');
        }
        scrollToBottom(); // Ensure scroll to bottom when chat is opened
    });

    $('#send-message').click(function() {
        if (!isSendingMessage) {
            isSendingMessage = true;
            sendMessage();
        }
    });

    $('#message-input').on('input', function() {
        autoGrow(this);
        toggleSendButton();
    });

    $('#message-input').keypress(function(e) {
        if (e.which == 13 && !e.shiftKey && !isSendingMessage) {
            isSendingMessage = true;
            sendMessage();
            e.preventDefault();
        }
    });

    function sendMessage() {
        const message = $('#message-input').val().trim();
        if (message === '') return;

        displayMessage(message, 'user');
        $('#message-input').val('');
        autoGrow($('#message-input')[0]);
        toggleSendButton();
        displayTypingIndicator();
        setInputEnabled(false);

        $.ajax({
            url: '/send_message',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: message }),
            success: function(response) {
                removeTypingIndicator();
                setInputEnabled(true);
                isSendingMessage = false;
                if (response.message) {
                    displayMessage(response.message, 'ai');
                    if (response.buttons && response.buttons.length > 0) {
                        displayButtons(response.buttons);
                    }
                } else {
                    displayMessage('MIA klarte ikke å finne et bra svar.', 'error');
                }
                scrollToBottom(); // Ensure scroll to bottom after receiving a message
            },
            error: function(xhr, status, error) {
                removeTypingIndicator();
                setInputEnabled(true);
                isSendingMessage = false;
                displayMessage('Feil: ' + xhr.responseText, 'error');
                scrollToBottom(); // Ensure scroll to bottom after an error
            }
        });
    }

    function displayInitialMessage() {
        displayLoadingMessage();
        setTimeout(function() {
            replaceLoadingMessage("Hei, mitt navn er Mia! Hvordan kan jeg hjelpe deg i dag?");
            scrollToBottom(); // Ensure scroll to bottom after initial message
        }, 2000);
    }

    function displayMessage(message, sender) {
        if (message.includes("{skjema}")) {
            const [textBeforeForm, textAfterForm] = message.split("{skjema}");
            if (textBeforeForm.trim()) {
                let messageContainer = createMessage(textBeforeForm.trim(), sender);
                $('#messages-container').append(messageContainer);
                removeNewMessageClass(messageContainer);
            }
            displayForm();
            if (textAfterForm.trim()) {
                let messageContainer = createMessage(textAfterForm.trim(), sender);
                $('#messages-container').append(messageContainer);
                removeNewMessageClass(messageContainer);
            }
        } else {
            let messageContainer = createMessage(message, sender);
            $('#messages-container').append(messageContainer);
            removeNewMessageClass(messageContainer);
        }
        scrollToBottom(); // Ensure scroll to bottom after displaying a message
    }

    function displayButtons(buttons) {
        const buttonsHtml = buttons.map(button => {
            return `<button onclick="window.open('${button.link}', '_blank')">${button.label}</button>`;
        }).join(' ');

        const buttonContainerHtml = `
            <div class="message-container button-message-container">
                <div class="button-message-text">
                    ${buttonsHtml}
                </div>
            </div>
        `;
        $('#messages-container').append(buttonContainerHtml);
        scrollToBottom(); // Ensure scroll to bottom after displaying buttons
    }

    function displayForm() {
        let formHtml = `
            <div class="message-container form-message-container">
                <div class="form-message-text">
                    <form id="contact-form">
                        <label for="email">E-post:</label><br>
                        <input type="email" id="email" name="email" required><br><br>
                        <label for="message">Melding:</label><br>
                        <textarea id="message" name="message" rows="4" required></textarea><br><br>
                        <button id="ai-form-button" type="submit">Send</button>
                    </form>
                </div>
            </div>
        `;
        $('#messages-container').append(formHtml);
        scrollToBottom(); // Ensure scroll to bottom after displaying form

        $('#contact-form').submit(function(e) {
            e.preventDefault();
            let email = $('#email').val().trim();
            let message = $('#message').val().trim();
            if (email && message) {
                showSpinner();
                $.ajax({
                    url: '/submit_form',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ email: email, message: message }),
                    success: function(response) {
                        alert(response.message);
                        removeSpinner();
                        displayMessage("Tusen takk! Meldingen din har blitt sendt:) En av våre kunderepresentanter tar kontakt med deg så raskt som mulig", 'ai');
                        scrollToBottom(); // Ensure scroll to bottom after form submission success
                    },
                    error: function(xhr, status, error) {
                        alert('Failed to send email: ' + xhr.responseText);
                        removeSpinner();
                        scrollToBottom(); // Ensure scroll to bottom after form submission error
                    }
                });
            }
        });
    }

    function showSpinner() {
        let spinnerHtml = `
            <div class="message-container ai-message spinner-container">
                <div class="spinner"></div>
            </div>
        `;
        $('#messages-container').append(spinnerHtml);
        scrollToBottom(); // Ensure scroll to bottom after showing spinner
    }

    function removeSpinner() {
        $('.spinner-container').remove();
        scrollToBottom(); // Ensure scroll to bottom after removing spinner
    }

    function createMessage(messageText, sender) {
        let messageClass = sender === 'user' ? 'user-message' : 'ai-message';
        let messageId = 'message-' + Date.now();
        let formattedMessage = marked.parse(messageText);
        return `<div id="${messageId}" class="message-container ${messageClass} new-message"><div class="message-text">${formattedMessage}</div></div>`;
    }

    function removeNewMessageClass(messageContainer) {
        setTimeout(function() {
            $(messageContainer).removeClass('new-message');
        }, 500);
        scrollToBottom(); // Ensure scroll to bottom after removing new message class
    }

    function displayTypingIndicator() {
        displayLoadingMessage();
    }

    function displayLoadingMessage() {
        $('#messages-container').append('<div class="message-container ai-message loading-message"><div class="message-text"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div></div>');
        scrollToBottom(); // Ensure scroll to bottom after displaying loading message
    }

    function replaceLoadingMessage(text) {
        $('.loading-message').first().replaceWith('<div class="message-container ai-message"><div class="message-text">' + text + '</div></div>');
        scrollToBottom(); // Ensure scroll to bottom after replacing loading message
    }

    function removeTypingIndicator() {
        $('#messages-container .loading-message').remove();
        scrollToBottom(); // Ensure scroll to bottom after removing typing indicator
    }

    function scrollToBottom() {
        const messagesContainer = $('#messages-container');
        messagesContainer.scrollTop(messagesContainer.prop("scrollHeight"));
    }

    function setInputEnabled(enabled) {
        $('#message-input').prop('disabled', !enabled);
        $('#send-message').prop('disabled', !enabled);
        if (enabled) {
            $('#message-input').focus();
        }
    }

    function autoGrow(element) {
        element.style.height = "5px";
        element.style.height = (element.scrollHeight) + "px";
        if (element.scrollHeight <= 40) {
            element.style.height = "40px";
        }
    }

    function toggleSendButton() {
        const message = $('#message-input').val().trim();
        if (message === '') {
            $('#send-message').css('opacity', '0.2');
        } else {
            $('#send-message').css('opacity', '1');
        }
    }

    toggleSendButton();
    checkInitialMessageStatus(); // Ensure initial status is checked on load
});
