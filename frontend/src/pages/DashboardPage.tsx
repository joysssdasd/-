import { FormEvent, useEffect, useMemo, useState } from 'react';
import api from '../api';
import { TRADE_TYPE_OPTIONS } from '../constants';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../context/ToastContext';
import CreatePostForm from '../components/CreatePostForm';
import PostList from '../components/PostList';
import dayjs from '../dayjs';
import { ContactView, DashboardData, Pagination, PointTransaction, PostListItem } from '../types';

const DashboardPage = () => {
  const { user, logout, refreshUser } = useAuth();
  const toast = useToast();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [posts, setPosts] = useState<PostListItem[]>([]);
  const [filters, setFilters] = useState({ keyword: '', tradeType: '', sort: 'deal_rate' });
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [contactViews, setContactViews] = useState<Record<number, ContactView>>({});
  const [transactions, setTransactions] = useState<PointTransaction[]>([]);
  const [selectedPost, setSelectedPost] = useState<PostListItem | null>(null);

  const loadDashboard = async () => {
    try {
      const { data } = await api.get<DashboardData>('/api/v1/users/dashboard');
      setDashboard(data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadPosts = async () => {
    setLoadingPosts(true);
    try {
      const params: Record<string, any> = { limit: 20 };
      if (filters.keyword) params['keyword'] = filters.keyword;
      if (filters.tradeType) params['trade_type'] = Number(filters.tradeType);
      if (filters.sort === 'created_at') params['sort_by'] = 'created_at';
      const { data } = await api.get<Pagination<PostListItem>>('/api/v1/posts', { params });
      setPosts(data.items);
    } catch (error) {
      console.error(error);
      toast.show('获取列表失败');
    } finally {
      setLoadingPosts(false);
    }
  };

  const loadTransactions = async () => {
    try {
      const { data } = await api.get<PointTransaction[]>('/api/v1/points/transactions');
      setTransactions(data.slice(0, 5));
    } catch (error) {
      console.error(error);
    }
  };

  const handleFilterSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    loadPosts();
  };

  const handleViewContact = async (post: PostListItem) => {
    try {
      const { data } = await api.post<ContactView>(`/api/v1/posts/${post.id}/contact`);
      setContactViews((prev) => ({ ...prev, [post.id]: data }));
      try {
        await navigator.clipboard.writeText(post.owner.wechat_id);
        toast.show(`微信号 ${post.owner.wechat_id} 已复制`);
      } catch {
        toast.show(`微信号：${post.owner.wechat_id}`);
      }
      await Promise.all([loadDashboard(), loadTransactions(), loadPosts()]);
      await refreshUser();
    } catch (error: any) {
      toast.show(error?.response?.data?.detail ?? '查看失败');
    }
  };

  const handleConfirmDeal = async (post: PostListItem, contact: ContactView, isDeal: boolean) => {
    try {
      const { data } = await api.post<ContactView>(`/api/v1/posts/${post.id}/contact/${contact.id}/confirm`, { is_deal: isDeal });
      setContactViews((prev) => ({ ...prev, [post.id]: data }));
      toast.show(isDeal ? '感谢反馈，已更新成交率' : '已记录为未成交');
      await loadDashboard();
    } catch (error: any) {
      toast.show(error?.response?.data?.detail ?? '反馈失败');
    }
  };

  useEffect(() => {
    loadDashboard();
    loadPosts();
    loadTransactions();
  }, []);

  useEffect(() => {
    if (!selectedPost) return;
    const updated = posts.find((post) => post.id === selectedPost.id);
    if (updated && updated !== selectedPost) {
      setSelectedPost(updated);
    }
  }, [posts, selectedPost]);

  const currentContact = useMemo(() => {
    if (!selectedPost) return null;
    return contactViews[selectedPost.id] ?? null;
  }, [contactViews, selectedPost]);

  return (
    <>
      <header className="header">
        <h1>欢迎回来，{user?.phone}</h1>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="secondary" onClick={() => window.location.reload()}>刷新</button>
          <button className="secondary" onClick={logout}>退出登录</button>
        </div>
      </header>
      <main className="main-content">
        <section className="card">
          <h2>我的数据总览</h2>
          {dashboard ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginTop: 16 }}>
              <div className="card" style={{ marginBottom: 0, background: '#007aff', color: '#fff' }}>
                <p style={{ margin: 0, fontSize: 14 }}>可用积分</p>
                <p style={{ margin: '8px 0 0', fontSize: 28 }}>{dashboard.points}</p>
              </div>
              <div className="card" style={{ marginBottom: 0 }}>
                <p style={{ margin: 0, fontSize: 14, color: '#6b7280' }}>成交率</p>
                <p style={{ margin: '8px 0 0', fontSize: 24 }}>{dashboard.deal_rate.toFixed(1)}%</p>
              </div>
              <div className="card" style={{ marginBottom: 0 }}>
                <p style={{ margin: 0, fontSize: 14, color: '#6b7280' }}>发布总量</p>
                <p style={{ margin: '8px 0 0', fontSize: 24 }}>{dashboard.total_posts}</p>
              </div>
              <div className="card" style={{ marginBottom: 0 }}>
                <p style={{ margin: 0, fontSize: 14, color: '#6b7280' }}>上架中</p>
                <p style={{ margin: '8px 0 0', fontSize: 24 }}>{dashboard.active_posts}</p>
              </div>
            </div>
          ) : (
            <p>加载中...</p>
          )}
        </section>

        <section className="card">
          <h2>快速发布信息</h2>
          <p style={{ color: '#6b7280', marginBottom: 20 }}>填写表单并提交，系统将自动扣除10积分并上架72小时。</p>
          <CreatePostForm onSuccess={async () => {
            await Promise.all([loadDashboard(), loadPosts(), loadTransactions()]);
          }} />
        </section>

        <section className="card">
          <h2>信息广场</h2>
          <form className="form-grid two-column" onSubmit={handleFilterSubmit} style={{ marginBottom: 16 }}>
            <label>
              关键词搜索
              <input value={filters.keyword} onChange={(event) => setFilters((prev) => ({ ...prev, keyword: event.target.value }))} placeholder="标题或关键词" />
            </label>
            <label>
              交易类型
              <select value={filters.tradeType} onChange={(event) => setFilters((prev) => ({ ...prev, tradeType: event.target.value }))}>
                <option value="">全部</option>
                {TRADE_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              排序方式
              <select value={filters.sort} onChange={(event) => setFilters((prev) => ({ ...prev, sort: event.target.value }))}>
                <option value="deal_rate">成交率优先</option>
                <option value="created_at">最新发布</option>
              </select>
            </label>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button type="submit" className="primary" disabled={loadingPosts}>
                {loadingPosts ? '加载中...' : '开始筛选'}
              </button>
            </div>
          </form>
          <PostList
            posts={posts}
            onViewDetail={(post) => setSelectedPost(post)}
            onViewContact={handleViewContact}
          />
        </section>

        {selectedPost && (
          <section className="card">
            <h2>信息详情</h2>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <h3>{selectedPost.title}</h3>
                <p style={{ color: '#6b7280' }}>发布人微信：{selectedPost.owner.wechat_id}</p>
                <p style={{ color: '#6b7280' }}>发布时间：{dayjs(selectedPost.created_at).format('YYYY-MM-DD HH:mm')}</p>
              </div>
              <button className="secondary" onClick={() => setSelectedPost(null)}>关闭</button>
            </div>
            <p>关键词：{selectedPost.keywords}</p>
            <p>价格：¥{Number(selectedPost.price).toFixed(2)}</p>
            {selectedPost.delivery_date && <p>交割时间：{dayjs(selectedPost.delivery_date).format('YYYY-MM-DD')}</p>}
            {selectedPost.extra_info && <p>补充信息：{selectedPost.extra_info}</p>}
            <p>剩余查看次数：{selectedPost.view_limit - selectedPost.view_count}</p>
            {currentContact ? (
              <div style={{ marginTop: 16 }}>
                <p>你已于 {dayjs(currentContact.created_at).format('YYYY-MM-DD HH:mm')} 查看联系方式。</p>
                {!currentContact.has_confirmed ? (
                  <div style={{ display: 'flex', gap: 12 }}>
                    <button className="primary" onClick={() => handleConfirmDeal(selectedPost, currentContact, true)}>标记成交</button>
                    <button className="secondary" onClick={() => handleConfirmDeal(selectedPost, currentContact, false)}>暂未成交</button>
                  </div>
                ) : (
                  <p style={{ color: '#34c759' }}>{currentContact.is_deal ? '已标记成交 ✅' : '已反馈未成交'}</p>
                )}
              </div>
            ) : (
              <p style={{ color: '#6b7280' }}>提示：点击“查看联系方式”将扣除1积分。</p>
            )}
          </section>
        )}

        <section className="card">
          <h2>积分流水（最近5条）</h2>
          {transactions.length ? (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {transactions.map((tx) => (
                <li key={tx.id} style={{ padding: '12px 0', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <p style={{ margin: 0, fontWeight: 600 }}>{tx.description}</p>
                    <small style={{ color: '#6b7280' }}>{dayjs(tx.created_at).format('YYYY-MM-DD HH:mm')}</small>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ margin: 0, color: tx.change_amount > 0 ? '#34c759' : '#ef4444' }}>
                      {tx.change_amount > 0 ? `+${tx.change_amount}` : tx.change_amount}
                    </p>
                    <small style={{ color: '#6b7280' }}>余额：{tx.balance_after}</small>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: '#6b7280' }}>暂无积分记录。</p>
          )}
        </section>
      </main>
    </>
  );
};

export default DashboardPage;
