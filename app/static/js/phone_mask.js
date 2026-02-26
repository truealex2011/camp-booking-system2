// Phone number masking component

class PhoneMask {
    constructor(inputElement) {
        this.input = inputElement;
        this.init();
    }
    
    init() {
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('paste', (e) => this.handlePaste(e));
        this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }
    
    handleInput(e) {
        let value = e.target.value;
        let formatted = this.applyMask(value);
        e.target.value = formatted;
    }
    
    handlePaste(e) {
        e.preventDefault();
        let pastedText = (e.clipboardData || window.clipboardData).getData('text');
        let formatted = this.applyMask(pastedText);
        this.input.value = formatted;
    }
    
    handleKeyDown(e) {
        // Allow: backspace, delete, tab, escape, enter
        if ([8, 9, 27, 13, 46].indexOf(e.keyCode) !== -1 ||
            // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
            (e.keyCode === 65 && e.ctrlKey === true) ||
            (e.keyCode === 67 && e.ctrlKey === true) ||
            (e.keyCode === 86 && e.ctrlKey === true) ||
            (e.keyCode === 88 && e.ctrlKey === true) ||
            // Allow: home, end, left, right
            (e.keyCode >= 35 && e.keyCode <= 39)) {
            return;
        }
        
        // Ensure that it is a number and stop the keypress
        if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();
        }
    }
    
    applyMask(value) {
        // Extract only digits
        let digits = value.replace(/\D/g, '');
        
        // Remove leading 7 or 8 if present
        if (digits.startsWith('7') || digits.startsWith('8')) {
            digits = digits.substring(1);
        }
        
        // Limit to 10 digits
        digits = digits.substring(0, 10);
        
        // Apply mask: +7 (XXX) XXX-XX-XX
        let formatted = '+7';
        
        if (digits.length > 0) {
            formatted += ' (' + digits.substring(0, 3);
        }
        
        if (digits.length >= 4) {
            formatted += ') ' + digits.substring(3, 6);
        }
        
        if (digits.length >= 7) {
            formatted += '-' + digits.substring(6, 8);
        }
        
        if (digits.length >= 9) {
            formatted += '-' + digits.substring(8, 10);
        }
        
        return formatted;
    }
    
    validate() {
        let value = this.input.value;
        let pattern = /^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$/;
        return pattern.test(value);
    }
}
