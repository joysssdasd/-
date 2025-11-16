import { createContext, useCallback, useContext, useMemo, useState } from 'react';

type ToastState = {
  message: string;
  visible: boolean;
};

type ToastContextValue = {
  show: (message: string) => void;
} & ToastState;

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ToastState>({ message: '', visible: false });

  const show = useCallback((message: string) => {
    setState({ message, visible: true });
    setTimeout(() => {
      setState({ message: '', visible: false });
    }, 2500);
  }, []);

  const value = useMemo(() => ({ ...state, show }), [state, show]);

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};
