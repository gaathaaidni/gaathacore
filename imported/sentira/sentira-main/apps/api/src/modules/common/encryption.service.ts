import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as crypto from 'crypto';

@Injectable()
export class EncryptionService implements OnModuleInit {
  private readonly logger = new Logger(EncryptionService.name);
  private key: Buffer;
  private readonly algorithm = 'aes-256-gcm';
  private readonly ivLength = 16;
  private readonly authTagLength = 16;

  constructor(private configService: ConfigService) {}

  onModuleInit() {
    const secret = this.configService.get<string>('CAMERA_CREDENTIAL_ENCRYPTION_KEY');
    if (!secret || secret.length < 32) {
      this.logger.error('CAMERA_CREDENTIAL_ENCRYPTION_KEY is not set or is too short. It must be at least 32 characters.');
      throw new Error('Invalid encryption key configuration.');
    }
    this.key = crypto.createHash('sha256').update(String(secret)).digest();
  }

  encrypt(text: string): string {
    const iv = crypto.randomBytes(this.ivLength);
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);
    const encrypted = Buffer.concat([cipher.update(text, 'utf8'), cipher.final()]);
    const authTag = cipher.getAuthTag();
    return Buffer.concat([iv, authTag, encrypted]).toString('hex');
  }

  decrypt(encryptedText: string): string {
    try {
      const data = Buffer.from(encryptedText, 'hex');
      const iv = data.slice(0, this.ivLength);
      const authTag = data.slice(this.ivLength, this.ivLength + this.authTagLength);
      const encrypted = data.slice(this.ivLength + this.authTagLength);
      const decipher = crypto.createDecipheriv(this.algorithm, this.key, iv);
      decipher.setAuthTag(authTag);
      const decrypted = Buffer.concat([decipher.update(encrypted), decipher.final()]);
      return decrypted.toString('utf8');
    } catch (error) {
      this.logger.error('Decryption failed. This may be due to an incorrect key or corrupted data.');
      return null;
    }
  }
}