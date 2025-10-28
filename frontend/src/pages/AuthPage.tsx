import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../context/ToastContext';

const AuthPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const toast = useToast();
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [wechatId, setWechatId] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [isRequestingCode, setIsRequestingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [showRegisterFields, setShowRegisterFields] = useState(false);

  const handleRequestCode = async () => {
    if (!/^\d{11}$/.test(phone)) {
      toast.show('请先输入11位手机号码');
      return;
    }
    setIsRequestingCode(true);
    try {
      const { data } = await api.post('/api/v1/auth/request-code', { phone });
      toast.show(`验证码: ${data.code}`);
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error: any) {
      toast.show(error?.response?.data?.detail ?? '验证码发送失败');
    } finally {
      setIsRequestingCode(false);
    }
  };

  const submit = async (event: FormEvent<HTMLFormElement>, mode: 'login' | 'register') => {
    event.preventDefault();
    if (!/^\d{11}$/.test(phone) || !/^\d{6}$/.test(code)) {
      toast.show('请检查手机号和验证码格式');
      return;
    }
    try {
      const payload: Record<string, string> = { phone, code };
      if (mode === 'register') {
        if (!wechatId) {
          toast.show('注册需要填写微信号');
          return;
        }
        payload['wechat_id'] = wechatId;
        if (inviteCode) {
          payload['invite_code'] = inviteCode;
        }
      }

      const endpoint = mode === 'register' ? '/api/v1/auth/register' : '/api/v1/auth/login';
      const { data } = await api.post(endpoint, payload);
      await login(data.access_token);
      toast.show('登录成功');
      navigate('/dashboard');
    } catch (error: any) {
      toast.show(error?.response?.data?.detail ?? '登录失败');
    }
  };

  return (
    <div className="main-content" style={{ maxWidth: 420 }}>
      <div className="card" style={{ marginTop: 60 }}>
        <h1 style={{ fontSize: 24, marginBottom: 8 }}>交易信息撮合平台</h1>
        <p style={{ color: '#6b7280', marginBottom: 24 }}>输入手机号获取验证码，注册或登录平台。</p>
        <form className="form-grid" onSubmit={(event) => submit(event, showRegisterFields ? 'register' : 'login')}>
          <label>
            手机号
            <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="请输入11位手机号" />
          </label>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <label style={{ flex: 1 }}>
              验证码
              <input value={code} onChange={(event) => setCode(event.target.value)} placeholder="6位数字" />
            </label>
            <button
              type="button"
              className="secondary"
              disabled={isRequestingCode || countdown > 0}
              onClick={handleRequestCode}
              style={{ width: 140 }}
            >
              {countdown > 0 ? `${countdown}s` : '获取验证码'}
            </button>
          </div>

          {showRegisterFields && (
            <>
              <label>
                微信号
                <input value={wechatId} onChange={(event) => setWechatId(event.target.value)} placeholder="6-20位字母数字" />
              </label>
              <label>
                邀请码（可选）
                <input value={inviteCode} onChange={(event) => setInviteCode(event.target.value)} placeholder="请输入邀请码" />
              </label>
            </>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <button type="submit" className="primary">
              {showRegisterFields ? '注册并登录' : '验证码登录'}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => setShowRegisterFields((prev) => !prev)}
            >
              {showRegisterFields ? '改为验证码登录' : '没有账号？点此注册'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;
