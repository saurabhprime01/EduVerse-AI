// EduVerse AI Voice Interaction Wrapper (HTML5 Speech API)
class EduVerseVoice {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.isSpeaking = false;
        this.voiceRate = 1.0; // Adjustable speed for children
        this.selectedVoice = null;
        
        this.initRecognition();
        this.initVoices();
    }

    initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.lang = 'en-US';
            this.recognition.interimResults = false;
            this.recognition.maxAlternatives = 1;
        } else {
            console.warn("Speech recognition is not supported in this browser.");
        }
    }

    initVoices() {
        if (!this.synthesis) return;
        
        const loadVoices = () => {
            const voices = this.synthesis.getVoices();
            // Try to find a child-friendly sounding voice (e.g. Google US English, Samantha, etc.)
            this.selectedVoice = voices.find(v => v.name.includes("Google US English") || v.name.includes("Natural") || v.name.includes("Zira")) || voices[0];
        };

        loadVoices();
        if (this.synthesis.onvoiceschanged !== undefined) {
            this.synthesis.onvoiceschanged = loadVoices;
        }
    }

    setVoiceSpeed(rate) {
        this.voiceRate = parseFloat(rate) || 1.0;
    }

    // Text-to-Speech (AI Speaking)
    speak(text, onStartCallback, onEndCallback) {
        if (!this.synthesis) return;

        // Cancel current utterance if speaking
        this.synthesis.cancel();

        // Strip HTML tags for clean reading
        const cleanText = text.replace(/<\/?[^>]+(>|$)/g, "");

        const utterance = new SpeechSynthesisUtterance(cleanText);
        if (this.selectedVoice) {
            utterance.voice = this.selectedVoice;
        }
        utterance.rate = this.voiceRate;
        utterance.pitch = 1.2; // Slightly higher pitch for child-friendly tone

        utterance.onstart = () => {
            this.isSpeaking = true;
            if (onStartCallback) onStartCallback();
        };

        utterance.onend = () => {
            this.isSpeaking = false;
            if (onEndCallback) onEndCallback();
        };

        utterance.onerror = (err) => {
            console.error("Speech synthesis error:", err);
            this.isSpeaking = false;
            if (onEndCallback) onEndCallback();
        };

        this.synthesis.speak(utterance);
    }

    // Speech-to-Text (Child Speaking)
    startListening(onResult, onEnd, onError) {
        if (!this.recognition) {
            if (onError) onError("Your browser doesn't support speaking with Buddy. Try Google Chrome!");
            return;
        }

        if (this.isListening) return;

        this.isListening = true;
        this.recognition.start();

        this.recognition.onresult = (event) => {
            const resultText = event.results[0][0].transcript;
            if (onResult) onResult(resultText);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            if (onEnd) onEnd();
        };

        this.recognition.onerror = (event) => {
            this.isListening = false;
            console.error("Speech recognition error:", event.error);
            if (onError) onError(event.error);
        };
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        }
    }

    stopSpeaking() {
        if (this.synthesis && this.isSpeaking) {
            this.synthesis.cancel();
            this.isSpeaking = false;
        }
    }
}

// Global initialization
window.eduverseVoice = new EduVerseVoice();
