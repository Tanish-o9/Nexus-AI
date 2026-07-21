'use client';

import { useState } from 'react';
import { useSelector, TypedUseSelectorHook } from 'react-redux';
import { RootState } from '@/store';

const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
import { Button } from '@/components/ui/button';
import {
  User, Building2, Bell, Shield, Palette, Key, Check, Sparkles, Loader2, Save
} from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const user = useAppSelector((state) => state.auth.user);
  const [activeTab, setActiveTab] = useState<'profile' | 'organization' | 'notifications' | 'security' | 'appearance'>('profile');

  // Form states
  const [username, setUsername] = useState(user?.username || 'Tanish');
  const [fullName, setFullName] = useState('Tanish Rajput');
  const [email, setEmail] = useState(user?.email || 'tanishrajput673@gmail.com');
  const [jobTitle, setJobTitle] = useState('Lead Product Engineer & Owner');
  const [department, setDepartment] = useState('Engineering & Core Product');
  const [bio, setBio] = useState('Building next-gen project management & AI tools on the Nexus PM platform.');
  const [timezone, setTimezone] = useState('Asia/Kolkata (IST - UTC +05:30)');
  const [phone, setPhone] = useState('+91 98765 43210');
  const [githubHandle, setGithubHandle] = useState('tanish-rajput');
  const [isSaving, setIsSaving] = useState(false);

  // Security states
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // Notification toggles
  const [notifyTaskAssign, setNotifyTaskAssign] = useState(true);
  const [notifyGithubPush, setNotifyGithubPush] = useState(true);
  const [notifySprintReports, setNotifySprintReports] = useState(true);

  const handleSaveProfile = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      toast.success('Profile settings updated successfully!');
    }, 600);
  };

  const handleSavePassword = () => {
    if (!currentPassword || !newPassword) {
      toast.error('Please enter both current and new password');
      return;
    }
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      setCurrentPassword('');
      setNewPassword('');
      toast.success('Password updated successfully!');
    }, 600);
  };

  return (
    <div className="flex flex-col gap-6 p-8 max-w-6xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-slate-100">Settings</h2>
        <p className="text-sm text-slate-400 mt-0.5">Manage your account preferences, security, and workspace</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Navigation Tabs Sidebar */}
        <div className="flex flex-col gap-1.5 bg-slate-900/40 border border-slate-800 rounded-xl p-3 h-fit">
          <TabButton
            icon={<User className="h-4 w-4" />}
            label="Profile & Account"
            active={activeTab === 'profile'}
            onClick={() => setActiveTab('profile')}
          />
          <TabButton
            icon={<Building2 className="h-4 w-4" />}
            label="Organization"
            active={activeTab === 'organization'}
            onClick={() => setActiveTab('organization')}
          />
          <TabButton
            icon={<Bell className="h-4 w-4" />}
            label="Notifications"
            active={activeTab === 'notifications'}
            onClick={() => setActiveTab('notifications')}
          />
          <TabButton
            icon={<Shield className="h-4 w-4" />}
            label="Security & Password"
            active={activeTab === 'security'}
            onClick={() => setActiveTab('security')}
          />
          <TabButton
            icon={<Palette className="h-4 w-4" />}
            label="Appearance"
            active={activeTab === 'appearance'}
            onClick={() => setActiveTab('appearance')}
          />
        </div>

        {/* Tab Content Panel */}
        <div className="md:col-span-3 glass-card-3d rounded-2xl p-7 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
          {activeTab === 'profile' && (
            <div className="flex flex-col gap-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">User Profile & Account Info</h3>
                <p className="text-xs text-slate-400">Manage your personal information, job title, bio, and account metadata</p>
              </div>

              {/* Header Profile Badge */}
              <div className="flex flex-wrap items-center justify-between gap-4 py-4 px-5 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-full bg-gradient-to-tr from-indigo-600 via-violet-600 to-purple-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-indigo-500/20">
                    {username.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-base font-bold text-slate-100">{fullName}</h4>
                      <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        Verified Owner
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">@{username} • {email}</p>
                    <p className="text-xs text-indigo-400 font-medium mt-0.5">{jobTitle}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-300">
                  <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                  <span>Member since <b>July 2026</b></span>
                </div>
              </div>

              {/* Account Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <MetricCard title="System Role" value="Admin / Owner" color="text-indigo-400" />
                <MetricCard title="Active Projects" value="1 Project (Lol)" color="text-emerald-400" />
                <MetricCard title="Tasks Completed" value="1 Task" color="text-violet-400" />
                <MetricCard title="Account Status" value="Active" color="text-teal-400" />
              </div>

              {/* Personal Details Form */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Contact Phone</label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Job Title / Role</label>
                  <input
                    type="text"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Department / Team</label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Timezone</label>
                  <input
                    type="text"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">GitHub Handle</label>
                  <input
                    type="text"
                    value={githubHandle}
                    onChange={(e) => setGithubHandle(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Bio / Summary</label>
                  <textarea
                    rows={3}
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 outline-none focus:border-indigo-500/50 resize-none"
                  />
                </div>
              </div>

              <Button
                onClick={handleSaveProfile}
                disabled={isSaving}
                className="bg-indigo-600 hover:bg-indigo-700 text-white self-start mt-2"
              >
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <Save className="h-4 w-4 mr-1.5" />}
                Save User Profile
              </Button>
            </div>
          )}

          {activeTab === 'organization' && (
            <div className="flex flex-col gap-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Organization Settings</h3>
                <p className="text-xs text-slate-400">Workspace settings and member roles</p>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Building2 className="h-5 w-5 text-indigo-400" />
                    <div>
                      <h4 className="text-sm font-semibold text-slate-200">Default Workspace</h4>
                      <p className="text-xs text-slate-500">Primary organization for your projects</p>
                    </div>
                  </div>
                  <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                    Active Owner
                  </span>
                </div>
              </div>

              <div className="flex flex-col gap-3">
                <h4 className="text-sm font-semibold text-slate-200">Workspace Members</h4>
                <div className="flex items-center justify-between py-2.5 border-b border-slate-800/80">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-indigo-500/20 text-indigo-400 font-bold flex items-center justify-center text-xs">
                      T
                    </div>
                    <div>
                      <p className="text-xs font-medium text-slate-200">Tanish (You)</p>
                      <p className="text-[11px] text-slate-500">tanishrajput673@gmail.com</p>
                    </div>
                  </div>
                  <span className="text-xs text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-md">Owner</span>
                </div>

                <div className="flex items-center justify-between py-2.5">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-violet-500/20 text-violet-400 font-bold flex items-center justify-center text-xs">
                      A
                    </div>
                    <div>
                      <p className="text-xs font-medium text-slate-200">ashutosh</p>
                      <p className="text-[11px] text-slate-500">ashutosh@gmail.com</p>
                    </div>
                  </div>
                  <span className="text-xs text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-md">Member</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="flex flex-col gap-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Notification Preferences</h3>
                <p className="text-xs text-slate-400">Choose what updates you receive</p>
              </div>

              <div className="flex flex-col gap-4">
                <ToggleItem
                  title="Task Assignment Alerts"
                  description="Receive instant notifications when assigned to a Kanban task"
                  checked={notifyTaskAssign}
                  onChange={setNotifyTaskAssign}
                />
                <ToggleItem
                  title="GitHub Integration Activity"
                  description="Notify when team members push code commits to connected repositories"
                  checked={notifyGithubPush}
                  onChange={setNotifyGithubPush}
                />
                <ToggleItem
                  title="Sprint & Weekly Reports"
                  description="Get auto-generated summary reports every week"
                  checked={notifySprintReports}
                  onChange={setNotifySprintReports}
                />
              </div>

              <Button
                onClick={() => toast.success('Notification preferences saved!')}
                className="bg-indigo-600 hover:bg-indigo-700 text-white self-start mt-2"
              >
                Save Preferences
              </Button>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="flex flex-col gap-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Security & Credentials</h3>
                <p className="text-xs text-slate-400">Update password and secret tokens</p>
              </div>

              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">Current Password</label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 mb-1.5 block">New Password</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500/50"
                  />
                </div>

                <Button
                  onClick={handleSavePassword}
                  disabled={isSaving}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white self-start mt-2"
                >
                  {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <Key className="h-4 w-4 mr-1.5" />}
                  Update Password
                </Button>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="flex flex-col gap-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100">Appearance & Theme</h3>
                <p className="text-xs text-slate-400">Customize visual theme and interface</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="border border-indigo-500/50 bg-slate-950 p-4 rounded-xl flex items-center justify-between cursor-pointer shadow-lg shadow-indigo-500/10">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center">
                      <Sparkles className="h-4 w-4 text-indigo-400" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-100">Midnight Dark</h4>
                      <p className="text-[11px] text-slate-400">Deep slate dark mode with glassmorphism</p>
                    </div>
                  </div>
                  <Check className="h-4 w-4 text-indigo-400" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({
  icon, label, active, onClick
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all text-left ${
        active
          ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
          : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function MetricCard({
  title, value, color
}: {
  title: string;
  value: string;
  color: string;
}) {
  return (
    <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
      <p className="text-[11px] font-medium text-slate-500">{title}</p>
      <p className={`text-xs font-bold ${color} mt-1`}>{value}</p>
    </div>
  );
}

function ToggleItem({
  title, description, checked, onChange
}: {
  title: string;
  description: string;
  checked: boolean;
  onChange: (val: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-800/80">
      <div>
        <h4 className="text-xs font-semibold text-slate-200">{title}</h4>
        <p className="text-[11px] text-slate-500">{description}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`w-11 h-6 rounded-full transition-colors relative flex items-center p-0.5 ${
          checked ? 'bg-indigo-600' : 'bg-slate-800'
        }`}
      >
        <div
          className={`w-5 h-5 rounded-full bg-white transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}
