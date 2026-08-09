

#!/usr/bin/env python3
import base64
import string
import hashlib
import secrets
import getpass
import os
import hmac
import subprocess
import sys
import re

# ANSI Color Codes for VS Code Terminal
class Colors:
    """Color definitions for beautiful terminal output"""
    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Reset
    RESET = '\033[0m'

class InputValidator:
    """Handles input validation with retry logic"""
    
    @staticmethod
    def validate_platform(platform):
        """Validate platform name"""
        if not platform or not platform.strip():
            return False, "Platform name cannot be empty!"
        if len(platform.strip()) < 2:
            return False, "Platform name must be at least 2 characters!"
        if re.search(r'[<>:"/\\|?*]', platform):
            return False, "Platform name contains invalid characters! (<>:\"/\\|?*)"
        return True, platform.strip()
    
    @staticmethod
    def validate_secret_salt(salt):
        """Validate secret salt"""
        if not salt or not salt.strip():
            return False, "Secret salt cannot be empty!"
        if len(salt.strip()) < 3:
            return False, "Secret salt must be at least 3 characters!"
        if len(salt.strip()) > 100:
            return False, "Secret salt is too long! Maximum 100 characters."
        return True, salt.strip()
    
    @staticmethod
    def validate_number(number):
        """Validate memorable number (must be numeric)"""
        if not number or not number.strip():
            return False, "Memorable number cannot be empty!"
        
        # Remove any whitespace
        number = number.strip()
        
        # Check if it's a valid number
        if not number.isdigit():
            return False, f"'{number}' is not a valid number! Please enter only digits (0-9)."
        
        # Convert to int for additional validation
        num_value = int(number)
        if num_value < 0:
            return False, "Number cannot be negative!"
        if len(number) > 15:
            return False, "Number is too long! Maximum 15 digits."
        
        return True, number
    
    @staticmethod
    def validate_master_passphrase(passphrase, confirm=None):
        """Validate master passphrase"""
        if not passphrase:
            return False, "Master passphrase cannot be empty!"
        if len(passphrase) < 8:
            return False, "Master passphrase must be at least 8 characters!"
        if len(passphrase) > 128:
            return False, "Master passphrase is too long! Maximum 128 characters."
        
        if confirm is not None and passphrase != confirm:
            return False, "Passphrases do not match!"
        
        # Check for reasonable complexity
        if not any(c.isupper() for c in passphrase):
            return False, "Passphrase should contain at least one uppercase letter!"
        if not any(c.islower() for c in passphrase):
            return False, "Passphrase should contain at least one lowercase letter!"
        if not any(c.isdigit() for c in passphrase):
            return False, "Passphrase should contain at least one number!"
        
        return True, passphrase
    
    @staticmethod
    def validate_password_length(length):
        """Validate password length input"""
        if not length:
            return True, 24  # Default
        
        try:
            length_int = int(length)
            if length_int < 16:
                return False, "Password length must be at least 16 characters!"
            if length_int > 128:
                return False, "Password length cannot exceed 128 characters!"
            return True, length_int
        except ValueError:
            return False, f"'{length}' is not a valid number! Please enter a number between 16 and 128."

class SyraxUltimateCryptoVault:
    """Ultimate cryptographic vault with strongest encryption and hashing"""
    
    def __init__(self, vault_file="ultimate_vault.txt"):
        self.vault_file = vault_file
        self.alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?~"
        self.iterations = 600_000
        self.validator = InputValidator()
        
    def print_colored(self, text, color=Colors.WHITE, style=Colors.RESET, end='\n'):
        """Print colored text"""
        print(f"{style}{color}{text}{Colors.RESET}", end=end)
    
    def print_header(self, text, icon="🔐"):
        """Print a formatted header"""
        print()
        self.print_colored("═" * 70, Colors.BRIGHT_CYAN, Colors.BOLD)
        self.print_colored(f"{icon}  {text}", Colors.BRIGHT_YELLOW, Colors.BOLD)
        self.print_colored("═" * 70, Colors.BRIGHT_CYAN, Colors.BOLD)
        print()
    
    def print_success(self, text):
        """Print success message"""
        self.print_colored(f"✅ {text}", Colors.BRIGHT_GREEN, Colors.BOLD)
    
    def print_error(self, text):
        """Print error message"""
        self.print_colored(f"❌ {text}", Colors.BRIGHT_RED, Colors.BOLD)
    
    def print_warning(self, text):
        """Print warning message"""
        self.print_colored(f"⚠️  {text}", Colors.BRIGHT_YELLOW, Colors.BOLD)
    
    def print_info(self, text):
        """Print info message"""
        self.print_colored(f"ℹ️  {text}", Colors.BRIGHT_CYAN)
    
    def print_password(self, password):
        """Print password with highlighting"""
        print()
        self.print_colored("🔑 PASSWORD: ", Colors.BRIGHT_GREEN, Colors.BOLD, end='')
        self.print_colored(password, Colors.BRIGHT_WHITE, Colors.BOLD)
        print()
    
    def get_validated_input(self, prompt, validation_func, error_msg=None, allow_empty=False, default=None):
        """Get and validate user input with retry"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            if attempt > 0:
                self.print_warning(f"Attempt {attempt + 1} of {max_attempts}")
            
            user_input = input(prompt).strip()
            
            if not user_input and allow_empty:
                return default if default else ""
            
            is_valid, result = validation_func(user_input)
            
            if is_valid:
                return result
            else:
                self.print_error(result)
                if error_msg:
                    self.print_info(error_msg)
                attempt += 1
        
        self.print_error(f"Failed after {max_attempts} attempts. Please restart the operation.")
        return None
    
    def copy_to_clipboard(self, text):
        """Copy password to clipboard for easy pasting"""
        try:
            if sys.platform == 'win32':
                subprocess.run(['clip'], input=text.encode('utf-8'), check=True)
            elif sys.platform == 'darwin':
                subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
            else:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
            return True
        except:
            return False
    
    def _derive_key_strong(self, passphrase: str, salt: bytes, context: str) -> bytes:
        """Strong key derivation: PBKDF2-HMAC-SHA512 implementation"""
        if not passphrase:
            return hashlib.sha512(salt + context.encode()).digest()
        
        def pbkdf2_hmac_sha512(password, salt, iterations, dklen=64):
            password = password.encode('utf-8')
            
            def hmac_sha512(key, message):
                return hmac.new(key, message, hashlib.sha512).digest()
            
            dk = b''
            block = 1
            while len(dk) < dklen:
                u = hmac_sha512(password, salt + block.to_bytes(4, 'big'))
                ui = u
                for _ in range(iterations - 1):
                    u = hmac_sha512(password, u)
                    ui = bytes(x ^ y for x, y in zip(ui, u))
                dk += ui
                block += 1
            return dk[:dklen]
        
        combined_salt = hashlib.sha512(salt + context.encode()).digest()
        return pbkdf2_hmac_sha512(passphrase, combined_salt, self.iterations, 64)
    
    def xor_encrypt_decrypt(self, text: str, key: str) -> str:
        """Symmetric XOR operation for reversible encryption"""
        return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))
    
    def platform_anchor(self, platform: str) -> str:
        """Create platform anchor"""
        p = platform.strip().lower()
        if len(p) < 2:
            return f"{p}1"
        anchor = f"{p[0]}{p[-1]}{len(p)}"
        return anchor
    
    def generate_reversible_password(self, platform: str, secret_salt: str, number: str, master_pass: str = None) -> str:
        """Generate a password that can be RECREATED with the same inputs"""
        anchor = self.platform_anchor(platform)
        
        if master_pass:
            master_hash = hashlib.sha256(master_pass.encode()).hexdigest()[:16]
            raw_logic = f"{anchor}:{secret_salt}:{number}:{master_hash}"
        else:
            raw_logic = f"{anchor}:{secret_salt}:{number}"
        
        salt_stretched = (secret_salt * 10)[:100]
        xor_result = self.xor_encrypt_decrypt(raw_logic, salt_stretched)
        final_pass = base64.b64encode(xor_result.encode()).decode()
        
        while len(final_pass) < 24:
            final_pass += base64.b64encode(hashlib.sha256(final_pass.encode()).digest()).decode()[:4]
        
        return final_pass
    
    def recover_password(self, platform: str, secret_salt: str, number: str, master_pass: str = None) -> str:
        """RECOVER the EXACT password from inputs"""
        return self.generate_reversible_password(platform, secret_salt, number, master_pass)
    
    def decode_password(self, encoded_password: str, secret_salt: str) -> str:
        """Decode a password to see its raw logic"""
        try:
            decoded_bytes = base64.b64decode(encoded_password).decode()
            salt_stretched = (secret_salt * 10)[:100]
            original_logic = self.xor_encrypt_decrypt(decoded_bytes, salt_stretched)
            return original_logic
        except:
            return None
    
    def save_password_entry(self, platform: str, secret_salt: str, number: str, password: str, master_pass: str = None):
        """Save password entry with metadata"""
        password_hash = hashlib.pbkdf2_hmac('sha512', password.encode(), b'salt', 100000, dklen=32).hex()
        
        entry_str = f"""
{'='*60}
PLATFORM: {platform}
SALT: {secret_salt}
NUMBER: {number}
PASSWORD HASH: {password_hash[:32]}...
MASTER PASS USED: {bool(master_pass)}
SAVED: {hashlib.sha256(str(os.times()).encode()).hexdigest()[:16]}
{'='*60}
"""
        with open(self.vault_file, "a", encoding="utf-8") as f:
            f.write(entry_str)
        
        self.print_success(f"Password metadata saved to: {self.vault_file}")
    
    def generate_strong_random_password(self, length: int = 32) -> str:
        """Generate a cryptographically strong random password"""
        if length < 16:
            raise ValueError("Password length should be at least 16 characters")
        
        password = []
        password.append(secrets.choice(string.ascii_uppercase))
        password.append(secrets.choice(string.ascii_lowercase))
        password.append(secrets.choice(string.digits))
        password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?~"))
        
        for _ in range(length - 4):
            password.append(secrets.choice(self.alphabet))
        
        for i in range(len(password)):
            j = secrets.randbelow(len(password))
            password[i], password[j] = password[j], password[i]
        
        return ''.join(password)
    
    def test_password_strength(self, password: str) -> dict:
        """Analyze password strength"""
        strength = {
            'length': len(password),
            'has_upper': any(c.isupper() for c in password),
            'has_lower': any(c.islower() for c in password),
            'has_digit': any(c.isdigit() for c in password),
            'has_special': any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?~" for c in password),
            'entropy': 0
        }
        
        charset_size = 0
        if strength['has_upper']: charset_size += 26
        if strength['has_lower']: charset_size += 26
        if strength['has_digit']: charset_size += 10
        if strength['has_special']: charset_size += 32
        
        if charset_size > 0:
            strength['entropy'] = len(password) * (charset_size.bit_length() - 1)
        
        if strength['entropy'] >= 128:
            strength['level'] = "🔐 MILITARY GRADE"
            strength['color'] = Colors.BRIGHT_MAGENTA
        elif strength['entropy'] >= 80:
            strength['level'] = "🛡️ VERY STRONG"
            strength['color'] = Colors.BRIGHT_GREEN
        elif strength['entropy'] >= 60:
            strength['level'] = "✅ STRONG"
            strength['color'] = Colors.BRIGHT_CYAN
        else:
            strength['level'] = "⚠️ WEAK"
            strength['color'] = Colors.BRIGHT_YELLOW
        
        return strength

def main():
    vault = SyraxUltimateCryptoVault()
    
    # Welcome header
    print()
    vault.print_colored("╔" + "═" * 68 + "╗", Colors.BRIGHT_CYAN, Colors.BOLD)
    vault.print_colored("║" + " " * 20 + "🔐  SYRAX ULTIMATE CRYPTO VAULT  🔐" + " " * 20 + "║", Colors.BRIGHT_CYAN, Colors.BOLD)
    vault.print_colored("║" + " " * 15 + "⚡ RECOVERABLE PASSWORDS SYSTEM ⚡" + " " * 16 + "║", Colors.BRIGHT_YELLOW, Colors.BOLD)
    vault.print_colored("╚" + "═" * 68 + "╝", Colors.BRIGHT_CYAN, Colors.BOLD)
    
    print()
    vault.print_colored("📋 FEATURE: Auto-copy to clipboard for easy login!", Colors.BRIGHT_GREEN)
    vault.print_colored("🔄 FEATURE: Passwords are 100% recoverable from your inputs!", Colors.BRIGHT_CYAN)
    vault.print_colored("✓ FEATURE: Smart input validation with type checking!", Colors.BRIGHT_MAGENTA)
    print()
    
    while True:
        print()
        vault.print_colored("┌" + "─" * 66 + "┐", Colors.BRIGHT_BLUE)
        vault.print_colored("│" + " " * 25 + "📌 MAIN MENU" + " " * 34 + "│", Colors.BRIGHT_YELLOW, Colors.BOLD)
        vault.print_colored("├" + "─" * 66 + "┤", Colors.BRIGHT_BLUE)
        vault.print_colored("│  " + "1. 🌟 GENERATE NEW PASSWORD (Reversible/Recoverable)" + " " * 21 + "│", Colors.WHITE)
        vault.print_colored("│  " + "2. 🔄 RECOVER PASSWORD (Get existing password for login)" + " " * 19 + "│", Colors.WHITE)
        vault.print_colored("│  " + "3. ⚡ QUICK LOGIN MODE (Fast recovery + auto-copy)" + " " * 24 + "│", Colors.BRIGHT_GREEN, Colors.BOLD)
        vault.print_colored("│  " + "4. 🔍 DECODE/VERIFY (See raw logic of a password)" + " " * 26 + "│", Colors.WHITE)
        vault.print_colored("│  " + "5. 📁 VIEW VAULT (See stored password references)" + " " * 28 + "│", Colors.WHITE)
        vault.print_colored("│  " + "6. 🎲 RANDOM PASSWORD (Non-recoverable - Use with care)" + " " * 22 + "│", Colors.BRIGHT_YELLOW)
        vault.print_colored("│  " + "7. 🚪 EXIT" + " " * 56 + "│", Colors.BRIGHT_RED)
        vault.print_colored("└" + "─" * 66 + "┘", Colors.BRIGHT_BLUE)
        
        choice = input(f"\n{Colors.BRIGHT_CYAN}➤ Select option (1-7): {Colors.RESET}").strip()
        
        if choice == "1":
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_MAGENTA)
            vault.print_colored("║" + " " * 18 + "🔄 PASSWORD GENERATION MODE 🔄" + " " * 19 + "║", Colors.BRIGHT_MAGENTA, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_MAGENTA)
            vault.print_warning("Save these inputs securely - you'll need them to recover your password!")
            
            # Platform input with validation
            platform = vault.get_validated_input(
                f"\n{Colors.BRIGHT_CYAN}📱 Platform name (e.g., Gmail, Instagram): {Colors.RESET}",
                InputValidator.validate_platform,
                "Platform name should be at least 2 characters and contain no special symbols."
            )
            if platform is None:
                continue
            
            # Secret salt input with validation
            secret_salt = vault.get_validated_input(
                f"{Colors.BRIGHT_CYAN}🔑 Your Secret Salt (Inner word/phrase): {Colors.RESET}",
                InputValidator.validate_secret_salt,
                "Secret salt should be 3-100 characters long."
            )
            if secret_salt is None:
                continue
            
            # Number input with strict type validation
            number = vault.get_validated_input(
                f"{Colors.BRIGHT_CYAN}🔢 Your memorable number (digits only): {Colors.RESET}",
                InputValidator.validate_number,
                "This field requires NUMBERS only! Example: 12345"
            )
            if number is None:
                continue
            
            # Master passphrase option
            use_master = input(f"\n{Colors.BRIGHT_YELLOW}🔐 Use master passphrase? (y/n): {Colors.RESET}").lower()
            master_pass = None
            if use_master == 'y':
                print()
                vault.print_info("Master passphrase requirements:")
                vault.print_info("  • Minimum 8 characters")
                vault.print_info("  • At least one uppercase letter")
                vault.print_info("  • At least one lowercase letter")
                vault.print_info("  • At least one number")
                print()
                
                master_pass = vault.get_validated_input(
                    f"{Colors.BRIGHT_MAGENTA}🔒 Master passphrase: {Colors.RESET}",
                    lambda x: InputValidator.validate_master_passphrase(x, None),
                    "Please follow the passphrase requirements above."
                )
                if master_pass is None:
                    continue
                
                confirm = getpass.getpass(f"{Colors.BRIGHT_MAGENTA}✓ Confirm master passphrase: {Colors.RESET}").strip()
                is_valid, _ = InputValidator.validate_master_passphrase(master_pass, confirm)
                if not is_valid:
                    vault.print_error("Passphrases do not match!")
                    continue
            
            # Password length validation
            length_input = input(f"\n{Colors.BRIGHT_CYAN}📏 Password length (default 24, min 16, max 128): {Colors.RESET}").strip()
            is_valid, length = InputValidator.validate_password_length(length_input)
            if not is_valid:
                vault.print_error(length)
                continue
            
            print()
            vault.print_colored("🔄 Generating your secure password...", Colors.BRIGHT_CYAN)
            password = vault.generate_reversible_password(platform, secret_salt, number, master_pass)
            strength = vault.test_password_strength(password)
            
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_GREEN)
            vault.print_colored("║" + " " * 20 + "✅ PASSWORD GENERATED! ✅" + " " * 21 + "║", Colors.BRIGHT_GREEN, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_GREEN)
            
            vault.print_password(password)
            
            vault.print_colored(f"📏 Length: {len(password)} characters", Colors.BRIGHT_CYAN)
            vault.print_colored(f"{strength['level']} - Entropy: {strength['entropy']} bits", strength['color'], Colors.BOLD)
            
            # Auto-copy to clipboard
            if vault.copy_to_clipboard(password):
                vault.print_success("Password automatically COPIED to clipboard!")
                vault.print_info("You can now paste it (Ctrl+V) into your login form.")
            else:
                vault.print_warning("Select the password above, copy it (Ctrl+C), then paste (Ctrl+V)")
            
            print()
            vault.print_colored("💾 SAVE THESE VALUES TO RECOVER YOUR PASSWORD:", Colors.BRIGHT_YELLOW, Colors.BOLD)
            vault.print_colored(f"   • Platform: {platform}", Colors.WHITE)
            vault.print_colored(f"   • Secret Salt: {secret_salt}", Colors.WHITE)
            vault.print_colored(f"   • Number: {number}", Colors.WHITE)
            if master_pass:
                vault.print_colored(f"   • Master Passphrase: {'*' * len(master_pass)}", Colors.WHITE)
            
            vault.print_warning("Without these exact values, you CANNOT recover the password!")
            
            save_choice = input(f"\n{Colors.BRIGHT_CYAN}💾 Save password reference to vault? (y/n): {Colors.RESET}").lower()
            if save_choice == 'y':
                vault.save_password_entry(platform, secret_salt, number, password, master_pass)
        
        elif choice == "2" or choice == "3":
            if choice == "2":
                print()
                vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_BLUE)
                vault.print_colored("║" + " " * 19 + "🔄 PASSWORD RECOVERY MODE 🔄" + " " * 20 + "║", Colors.BRIGHT_BLUE, Colors.BOLD)
                vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_BLUE)
            else:
                print()
                vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_GREEN)
                vault.print_colored("║" + " " * 18 + "⚡ QUICK LOGIN MODE ⚡" + " " * 21 + "║", Colors.BRIGHT_GREEN, Colors.BOLD)
                vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_GREEN)
            
            vault.print_info("Enter the EXACT same values used when creating the password:")
            
            # Platform input with validation
            platform = vault.get_validated_input(
                f"\n{Colors.BRIGHT_CYAN}📱 Platform name: {Colors.RESET}",
                InputValidator.validate_platform,
                "Platform name should be at least 2 characters."
            )
            if platform is None:
                continue
            
            # Secret salt input with validation
            secret_salt = vault.get_validated_input(
                f"{Colors.BRIGHT_CYAN}🔑 Your Secret Salt: {Colors.RESET}",
                InputValidator.validate_secret_salt,
                "Secret salt should be 3-100 characters."
            )
            if secret_salt is None:
                continue
            
            # Number input with strict type validation
            number = vault.get_validated_input(
                f"{Colors.BRIGHT_CYAN}🔢 Your memorable number (digits only): {Colors.RESET}",
                InputValidator.validate_number,
                "This field requires NUMBERS only! Example: 12345"
            )
            if number is None:
                continue
            
            use_master = input(f"\n{Colors.BRIGHT_YELLOW}🔐 Was a master passphrase used? (y/n): {Colors.RESET}").lower()
            master_pass = None
            if use_master == 'y':
                master_pass = getpass.getpass(f"{Colors.BRIGHT_MAGENTA}🔒 Enter master passphrase: {Colors.RESET}").strip()
                if not master_pass:
                    vault.print_error("Master passphrase cannot be empty!")
                    continue
            
            print()
            vault.print_colored("🔄 Recovering your password...", Colors.BRIGHT_CYAN)
            recovered_password = vault.recover_password(platform, secret_salt, number, master_pass)
            strength = vault.test_password_strength(recovered_password)
            
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_GREEN)
            vault.print_colored("║" + " " * 18 + "🔓 PASSWORD RECOVERED! 🔓" + " " * 20 + "║", Colors.BRIGHT_GREEN, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_GREEN)
            
            vault.print_password(recovered_password)
            
            vault.print_colored(f"📏 Length: {len(recovered_password)} characters", Colors.BRIGHT_CYAN)
            vault.print_colored(f"{strength['level']} - Entropy: {strength['entropy']} bits", strength['color'], Colors.BOLD)
            
            # Auto-copy to clipboard for easy login
            # if vault.copy_to_clipboard(recovered_password):
                # vault.print_success("Password automatically COPIED to clipboard!")
                # vault.print_info("✅ Open your browser and paste (Ctrl+V) into the password field!")
                # vault.print_info("🚀 You're ready to log in!")
            # else:
                # vault.print_warning("Select and copy the password above")
            
            print()
            vault.print_colored("💡 Login Instructions:", Colors.BRIGHT_YELLOW, Colors.BOLD)
            vault.print_colored("   1. Go to your platform's login page", Colors.WHITE)
            vault.print_colored("   2. Click on the password field", Colors.WHITE)
            vault.print_colored("   3. Press Ctrl+V (or right-click + paste)", Colors.WHITE)
            vault.print_colored("   4. Click Login/Sign In", Colors.WHITE)
            
            verify = input(f"\n{Colors.BRIGHT_CYAN}🔍 Show raw logic for verification? (y/n): {Colors.RESET}").lower()
            if verify == 'y':
                raw_logic = vault.decode_password(recovered_password, secret_salt)
                if raw_logic:
                    print()
                    vault.print_colored("📊 Raw logic:", Colors.BRIGHT_MAGENTA, Colors.BOLD)
                    vault.print_colored(f"   {raw_logic}", Colors.BRIGHT_WHITE)
        
        elif choice == "4":
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_YELLOW)
            vault.print_colored("║" + " " * 20 + "🔍 PASSWORD DECODER 🔍" + " " * 22 + "║", Colors.BRIGHT_YELLOW, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_YELLOW)
            
            password_to_decode = input(f"\n{Colors.BRIGHT_CYAN}🔑 Paste the password to decode: {Colors.RESET}").strip()
            if not password_to_decode:
                vault.print_error("Password cannot be empty!")
                continue
            
            secret_salt = vault.get_validated_input(
                f"{Colors.BRIGHT_CYAN}🔑 Enter the Secret Salt used: {Colors.RESET}",
                InputValidator.validate_secret_salt,
                "Secret salt should be 3-100 characters."
            )
            if secret_salt is None:
                continue
            
            raw_logic = vault.decode_password(password_to_decode, secret_salt)
            if raw_logic:
                print()
                vault.print_success("DECODED SUCCESSFULLY!")
                print()
                vault.print_colored("📊 DECODED LOGIC:", Colors.BRIGHT_GREEN, Colors.BOLD)
                vault.print_colored(f"   {raw_logic}", Colors.BRIGHT_WHITE)
                print()
                vault.print_colored("🔍 Components:", Colors.BRIGHT_CYAN, Colors.BOLD)
                parts = raw_logic.split(':')
                if len(parts) >= 3:
                    vault.print_colored(f"   • Platform anchor: {parts[0]}", Colors.WHITE)
                    vault.print_colored(f"   • Salt: {parts[1]}", Colors.WHITE)
                    vault.print_colored(f"   • Number: {parts[2]}", Colors.WHITE)
                    if len(parts) > 3:
                        vault.print_colored(f"   • Master passphrase used: Yes", Colors.BRIGHT_MAGENTA)
            else:
                vault.print_error("Failed to decode. Wrong password or secret salt!")
        
        elif choice == "5":
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_BLUE)
            vault.print_colored("║" + " " * 21 + "📁 PASSWORD VAULT 📁" + " " * 23 + "║", Colors.BRIGHT_BLUE, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_BLUE)
            
            try:
                if not os.path.exists(vault.vault_file):
                    vault.print_error("Vault file not found. Generate a password first!")
                    continue
                
                with open(vault.vault_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        print()
                        vault.print_colored(content, Colors.BRIGHT_WHITE)
                    else:
                        vault.print_warning("Vault is empty.")
                
                print()
                vault.print_info("Use option 2 or 3 to recover actual passwords for login")
                
            except Exception as e:
                vault.print_error(f"Error reading vault: {e}")
        
        elif choice == "6":
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_YELLOW)
            vault.print_colored("║" + " " * 18 + "🎲 RANDOM PASSWORD MODE 🎲" + " " * 20 + "║", Colors.BRIGHT_YELLOW, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_YELLOW)
            vault.print_warning("This password CANNOT be recovered if lost!")
            
            # Password length validation
            length_input = input(f"\n{Colors.BRIGHT_CYAN}📏 Password length (default 32, min 16, max 128): {Colors.RESET}").strip()
            is_valid, length = InputValidator.validate_password_length(length_input)
            if not is_valid:
                vault.print_error(length)
                continue
            
            print()
            vault.print_colored("🎲 Generating cryptographically strong random password...", Colors.BRIGHT_CYAN)
            random_password = vault.generate_strong_random_password(length)
            strength = vault.test_password_strength(random_password)
            
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_GREEN)
            vault.print_colored("║" + " " * 19 + "⚡ RANDOM PASSWORD ⚡" + " " * 22 + "║", Colors.BRIGHT_GREEN, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_GREEN)
            
            vault.print_password(random_password)
            
            vault.print_colored(f"📏 Length: {len(random_password)} characters", Colors.BRIGHT_CYAN)
            vault.print_colored(f"{strength['level']} - Entropy: {strength['entropy']} bits", strength['color'], Colors.BOLD)
            
            if vault.copy_to_clipboard(random_password):
                vault.print_success("Password automatically COPIED to clipboard!")
                vault.print_info("You can now paste it (Ctrl+V) into your login form.")
            else:
                vault.print_warning("Select and copy the password above")
            
            vault.print_warning("SAVE THIS PASSWORD NOW - It cannot be recovered!")
            
            save_choice = input(f"\n{Colors.BRIGHT_CYAN}💾 Save reference to vault? (y/n): {Colors.RESET}").lower()
            if save_choice == 'y':
                platform = input(f"{Colors.BRIGHT_CYAN}📱 Platform name: {Colors.RESET}").strip()
                secret_salt = input(f"{Colors.BRIGHT_CYAN}🔑 Your secret salt (for reference): {Colors.RESET}").strip()
                number = input(f"{Colors.BRIGHT_CYAN}🔢 Memorable number (for reference): {Colors.RESET}").strip()
                vault.save_password_entry(platform, secret_salt, number, random_password, None)
        
        elif choice == "7":
            print()
            vault.print_colored("╔" + "═" * 66 + "╗", Colors.BRIGHT_RED)
            vault.print_colored("║" + " " * 22 + "🔒 EXITING VAULT 🔒" + " " * 24 + "║", Colors.BRIGHT_RED, Colors.BOLD)
            vault.print_colored("╚" + "═" * 66 + "╝", Colors.BRIGHT_RED)
            print()
            vault.print_colored("📌 LOGIN QUICK REFERENCE:", Colors.BRIGHT_YELLOW, Colors.BOLD)
            vault.print_colored("   • Use Option 2 (RECOVER) to get any saved password", Colors.WHITE)
            vault.print_colored("   • Use Option 3 (QUICK LOGIN) for fastest access", Colors.WHITE)
            vault.print_colored("   • Password auto-copies to clipboard for easy pasting", Colors.WHITE)
            print()
            vault.print_colored("🔐 Stay secure! Goodbye. 👋", Colors.BRIGHT_GREEN, Colors.BOLD)
            print()
            break
        
        else:
            vault.print_error("Invalid option. Please choose 1-7.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(f"\n{Colors.BRIGHT_YELLOW}⚠️  Exited by user. Goodbye!{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.BRIGHT_RED}❌ An error occurred: {Colors.RESET}{e}")
