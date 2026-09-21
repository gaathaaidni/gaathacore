import { IsBoolean, IsEmail, IsString, IsUUID, MinLength } from 'class-validator';

export class LoginDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;
}

export class LoginResponseDto {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    organizationId: string;
  };
}

export class RefreshDto { @IsString() refreshToken: string; }

export class SignupDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;

  @IsString()
  @MinLength(2)
  organizationName: string;

  @IsBoolean()
  termsAccepted: boolean;

  @IsBoolean()
  privacyAcknowledged: boolean;

  @IsUUID()
  termsDocumentId: string;

  @IsUUID()
  privacyDocumentId: string;
}

export class CurrentUserDto {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  organizationId: string;
  roleId: string;
}
