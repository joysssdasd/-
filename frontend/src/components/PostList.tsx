import dayjs from '../dayjs';
import { TRADE_TYPE_MAP } from '../constants';
import { PostListItem } from '../types';

export type PostListProps = {
  posts: PostListItem[];
  onViewDetail: (post: PostListItem) => void;
  onViewContact: (post: PostListItem) => void;
};

const PostList = ({ posts, onViewDetail, onViewContact }: PostListProps) => {
  if (!posts.length) {
    return <p style={{ color: '#6b7280' }}>暂无信息，试着调整筛选条件。</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {posts.map((post) => (
        <div key={post.id} className="post-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3>{post.title}</h3>
              <div className="post-meta">
                <span className="badge">{TRADE_TYPE_MAP[post.trade_type]}</span>
                <span>价格：¥{Number(post.price).toFixed(2)}</span>
                <span>成交率：{post.owner.deal_rate.toFixed(1)}%</span>
                <span>查看次数：{post.view_count}/{post.view_limit}</span>
                <span>发布时间：{dayjs(post.created_at).fromNow()}</span>
              </div>
            </div>
            <span className="status-pill">有效期至 {dayjs(post.expire_at).format('MM-DD HH:mm')}</span>
          </div>
          <p style={{ marginTop: 12, color: '#4b5563' }}>关键词：{post.keywords}</p>
          {post.extra_info && <p style={{ color: '#4b5563' }}>补充信息：{post.extra_info}</p>}
          <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
            <button className="secondary" onClick={() => onViewDetail(post)}>
              查看详情
            </button>
            <button className="primary" onClick={() => onViewContact(post)}>
              查看联系方式（-1积分）
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default PostList;
