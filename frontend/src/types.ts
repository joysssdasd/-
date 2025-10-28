export type DashboardData = {
  points: number;
  deal_rate: number;
  total_posts: number;
  active_posts: number;
};

export type PostListItem = {
  id: number;
  title: string;
  keywords: string;
  price: number;
  trade_type: number;
  delivery_date?: string | null;
  extra_info?: string | null;
  view_limit: number;
  view_count: number;
  deal_count: number;
  status: 'published' | 'unlisted' | 'expired';
  expire_at: string;
  created_at: string;
  updated_at: string;
  owner: {
    id: number;
    phone: string;
    wechat_id: string;
    deal_rate: number;
  };
};

export type Pagination<T> = {
  total: number;
  items: T[];
};

export type ContactView = {
  id: number;
  post_id: number;
  viewer_id: number;
  created_at: string;
  has_confirmed: boolean;
  is_deal: boolean;
};

export type PointTransaction = {
  id: number;
  change_type: string;
  change_amount: number;
  balance_after: number;
  related_id?: number | null;
  description: string;
  created_at: string;
};
