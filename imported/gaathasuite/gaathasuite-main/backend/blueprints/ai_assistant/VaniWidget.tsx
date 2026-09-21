import React, { useState, useEffect } from 'react';

const welcomeMessages = [
    "Welcome back. How can I assist you with your enterprise operations today?",
    "Vani is online. Ready to process your commands.",
    "Good morning. Let's optimize your workflow. What is our first objective?",
    "Vani reporting for duty. What is the most critical task I can execute for you right now?",
    "Welcome. The enterprise intelligence layer is active. How can I provide a strategic advantage?"
];

/**
 * A simple randomizer to pick a welcome message.
 * In a real application, this could be context-aware based on time of day,
 * recent user activity, or pending tasks.
 */
const getRandomWelcomeMessage = () => {
    const randomIndex = Math.floor(Math.random() * welcomeMessages.length);
    return welcomeMessages[randomIndex];
};

interface Message {
    sender: 'user' | 'Vani';
    text: string;
}

export const VaniWidget: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);

    useEffect(() => {
        // Set the initial welcome message when the component mounts.
        setMessages([
            { sender: 'Vani', text: getRandomWelcomeMessage() }
        ]);
    }, []);

    // In a real component, you would have methods here to handle user input
    // and make API calls to the `/ai-assistant/chat` backend endpoint.

    return (
        <div className="vani-chat-widget">
            <div className="message-list">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-bubble sender-${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
            </div>
            {/* Input form would go here */}
        </div>
    );
};