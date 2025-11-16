import { useToast } from '../context/ToastContext';

const Toast = () => {
  const { visible, message } = useToast();

  return (
    <div className={`toast ${visible ? 'show' : ''}`} role="status" aria-live="polite">
      {message}
    </div>
  );
};

export default Toast;
