import { FormEvent, useState } from 'react';
import dayjs from '../dayjs';
import api from '../api';
import { TRADE_TYPE_OPTIONS } from '../constants';
import { useToast } from '../context/ToastContext';

export type CreatePostFormProps = {
  onSuccess: () => void;
};

const CreatePostForm = ({ onSuccess }: CreatePostFormProps) => {
  const toast = useToast();
  const [title, setTitle] = useState('');
  const [keywords, setKeywords] = useState('');
  const [price, setPrice] = useState('');
  const [tradeType, setTradeType] = useState<number>(1);
  const [deliveryDate, setDeliveryDate] = useState('');
  const [extraInfo, setExtraInfo] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const reset = () => {
    setTitle('');
    setKeywords('');
    setPrice('');
    setTradeType(1);
    setDeliveryDate('');
    setExtraInfo('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!title || !keywords || !price) {
      toast.show('请完整填写标题、关键词和价格');
      return;
    }

    const payload: Record<string, any> = {
      title,
      keywords,
      price: Number(price),
      trade_type: tradeType
    };

    if ([3, 4].includes(tradeType)) {
      if (!deliveryDate) {
        toast.show('做多/做空需要选择交割时间');
        return;
      }
      if (!extraInfo) {
        toast.show('请补充策略说明，最多100字');
        return;
      }
      payload['delivery_date'] = dayjs(deliveryDate).format('YYYY-MM-DD');
    }

    if (extraInfo) {
      payload['extra_info'] = extraInfo;
    }

    setIsSubmitting(true);
    try {
      await api.post('/api/v1/posts', payload);
      toast.show('发布成功，已扣除积分');
      reset();
      onSuccess();
    } catch (error: any) {
      toast.show(error?.response?.data?.detail ?? '发布失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="form-grid two-column" onSubmit={handleSubmit}>
      <label>
        标题
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="30字以内" />
      </label>
      <label>
        关键词（逗号分隔）
        <input value={keywords} onChange={(event) => setKeywords(event.target.value)} placeholder="示例：手机,二手" />
      </label>
      <label>
        价格（元）
        <input type="number" value={price} onChange={(event) => setPrice(event.target.value)} min="0" step="0.01" />
      </label>
      <label>
        交易类型
        <select value={tradeType} onChange={(event) => setTradeType(Number(event.target.value))}>
          {TRADE_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      {[3, 4].includes(tradeType) && (
        <label>
          交割时间
          <input type="date" value={deliveryDate} onChange={(event) => setDeliveryDate(event.target.value)} min={dayjs().format('YYYY-MM-DD')} />
        </label>
      )}
      <label className="full-row">
        补充信息（可选，做多/做空必填）
        <textarea
          value={extraInfo}
          onChange={(event) => setExtraInfo(event.target.value)}
          placeholder="说明交易细节，例如交割方式、策略等"
          maxLength={100}
          rows={3}
        />
      </label>
      <div className="full-row" style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button className="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? '发布中...' : '发布信息（消耗10积分）'}
        </button>
      </div>
    </form>
  );
};

export default CreatePostForm;
