import React, { useState } from 'react';
import { DashboardLayout } from '../../../DashboardLayout';
import { Text } from '../../../Text';
import { Button } from '../../../Button';
import { ShieldCheck, Smartphone, Key, AlertCircle } from 'lucide-react';

export const SecuritySettings: React.FC = () => {
  const [isSetupVisible, setIsSetupVisible] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');

  return (
    <DashboardLayout>
      <div className="max-w-3xl flex flex-col gap-8">
        <div>
          <Text variant="h2">Security Settings</Text>
          <Text variant="caption">Enhance your account security with multi-factor authentication.</Text>
        </div>

        {/* 2FA Card */}
        <div className="bg-white rounded-2xl border border-gaatha-gray-100 shadow-sm overflow-hidden">
          <div className="p-6 flex items-start gap-4 border-b border-gaatha-gray-100">
            <div className="p-3 bg-gaatha-blue-50 text-gaatha-blue-600 rounded-xl">
              <Smartphone size={24} />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <Text variant="h3">Two-Factor Authentication (TOTP)</Text>
                <span className="bg-gaatha-gray-100 text-gaatha-gray-600 px-3 py-1 rounded-full text-xs font-bold uppercase">Disabled</span>
              </div>
              <Text variant="body" className="mt-1">
                Add an extra layer of security to your account by requiring a code from your authenticator app.
              </Text>
            </div>
          </div>

          {!isSetupVisible ? (
            <div className="p-6 bg-gaatha-gray-50/50">
              <Button variant="primary" onClick={() => setIsSetupVisible(true)}>Enable 2FA</Button>
            </div>
          ) : (
            <div className="p-8 flex flex-col gap-8 animate-in fade-in slide-in-from-top-4 duration-300">
              <div className="flex flex-col md:flex-row gap-8 items-center">
                <div className="w-48 h-48 bg-white border-4 border-gaatha-gray-100 rounded-xl flex items-center justify-center relative group">
                  <div className="absolute inset-0 bg-gaatha-gray-900/5 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Text variant="small" className="font-bold">MOCK QR CODE</Text>
                  </div>
                  <ShieldCheck size={100} className="text-gaatha-blue-600/20" />
                </div>
                
                <div className="flex-1 flex flex-col gap-4">
                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-gaatha-blue-600 text-white flex items-center justify-center text-xs font-bold">1</div>
                    <Text variant="body">Scan this QR code with your authenticator app (Google Authenticator, Authy, etc).</Text>
                  </div>
                  <div className="flex items-center gap-2 p-3 bg-gaatha-gray-50 rounded-lg border border-gaatha-gray-100">
                    <Key size={16} className="text-gaatha-gray-400" />
                    <Text variant="small" className="font-mono text-gaatha-gray-800">ABCD-EFGH-IJKL-MNOP</Text>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-4 pt-6 border-t border-gaatha-gray-100">
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-gaatha-blue-600 text-white flex items-center justify-center text-xs font-bold">2</div>
                  <Text variant="body">Enter the 6-digit code from your app to verify the setup.</Text>
                </div>
                
                <div className="flex gap-3 max-w-sm">
                  <input 
                    type="text"
                    maxLength={6}
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    placeholder="000000"
                    className="flex-1 px-4 py-2 bg-gaatha-gray-50 border border-gaatha-gray-200 rounded-lg font-mono text-center text-lg tracking-widest focus:ring-2 focus:ring-gaatha-blue-600 focus:bg-white outline-none transition-all"
                  />
                  <Button variant="primary">Verify & Enable</Button>
                </div>
              </div>
              
              <div className="flex gap-2 items-center text-gaatha-danger bg-gaatha-danger/5 p-3 rounded-lg">
                <AlertCircle size={16} />
                <Text variant="small" className="text-gaatha-danger">Ensure you save your backup codes in a safe place.</Text>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};