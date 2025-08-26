
// Helper function to convert strings to ArrayBuffer
const str2ab = (str: string) => {
    const buf = new ArrayBuffer(str.length);
    const bufView = new Uint8Array(buf);
    for (let i = 0, strLen = str.length; i < strLen; i++) {
        bufView[i] = str.charCodeAt(i);
    }
    return buf;
};

// Helper function to convert ArrayBuffer to string
const ab2str = (buf: ArrayBuffer) => {
    return String.fromCharCode.apply(null, Array.from(new Uint8Array(buf)));
};

// Derives a key from a password using PBKDF2
const getKey = async (password: string, salt: Uint8Array): Promise<CryptoKey> => {
    const keyMaterial = await window.crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(password),
        { name: 'PBKDF2' },
        false,
        ['deriveKey']
    );
    return window.crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: salt,
            iterations: 100000,
            hash: 'SHA-256',
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        true,
        ['encrypt', 'decrypt']
    );
};

/**
 * Encrypts a string using a password.
 * @param data The string to encrypt.
 * @param password The password to use for encryption.
 * @returns A base64 encoded string containing salt, iv, and ciphertext.
 */
export const encrypt = async (data: string, password: string): Promise<string> => {
    const salt = window.crypto.getRandomValues(new Uint8Array(16));
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const key = await getKey(password, salt);
    
    const encryptedContent = await window.crypto.subtle.encrypt(
        {
            name: 'AES-GCM',
            iv: iv,
        },
        key,
        new TextEncoder().encode(data)
    );

    const encryptedBytes = new Uint8Array(encryptedContent);
    const combined = new Uint8Array(salt.length + iv.length + encryptedBytes.length);
    combined.set(salt, 0);
    combined.set(iv, salt.length);
    combined.set(encryptedBytes, salt.length + iv.length);

    return btoa(ab2str(combined.buffer));
};

/**
 * Decrypts a base64 encoded string using a password.
 * @param encryptedData The base64 encoded string to decrypt.
 * @param password The password to use for decryption.
 * @returns The original decrypted string.
 */
export const decrypt = async (encryptedData: string, password:string): Promise<string> => {
    const combined = str2ab(atob(encryptedData));
    
    const salt = new Uint8Array(combined.slice(0, 16));
    const iv = new Uint8Array(combined.slice(16, 28));
    const encryptedBytes = new Uint8Array(combined.slice(28));
    
    const key = await getKey(password, salt);

    const decryptedContent = await window.crypto.subtle.decrypt(
        {
            name: 'AES-GCM',
            iv: iv,
        },
        key,
        encryptedBytes.buffer
    );

    return new TextDecoder().decode(decryptedContent);
};
