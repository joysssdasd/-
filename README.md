# 交易信息撮合平台

该仓库提供一个积分驱动的 C2C 交易信息撮合平台的完整参考实现与产品需求文档（PRD）。

## 📚 仓库结构概览

```
.
├── README.md                     # 项目介绍与使用说明
├── docs/
│   └── 交易信息撮合平台-产品需求文档.md  # 完整 PRD
└── backend/
    ├── app/                      # FastAPI 后端服务源码
    ├── requirements.txt          # 后端依赖列表
    └── tests/                    # 核心业务集成测试
```

## ⚙️ 后端服务快速启动

1. **安装依赖**

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **配置数据库连接**

   默认配置指向示例的 PostgreSQL 数据库。如果需要自建数据库，请在 `backend/.env` 中覆盖以下环境变量：

   ```dotenv
   DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>
   JWT_SECRET_KEY=<自定义密钥>
   ```

3. **启动服务**

   ```bash
   uvicorn app.main:app --reload
   ```

   启动后可访问 `http://127.0.0.1:8000/docs` 查看自动生成的 OpenAPI 文档。

## ✅ 功能要点

- 手机验证码注册 / 登录，支持邀请码关联与奖励。
- 用户积分体系（注册奖励、发布消耗、查看消耗、退还与邀请奖励）。
- 交易信息的发布、搜索、状态管理与联系方式查看。
- 成交确认与成交率自动计算。
- 后端集成测试覆盖核心流程，保障交易闭环稳定性。

## 🧪 运行测试

在项目根目录执行：

```bash
cd backend
pytest
```

测试会自动使用 SQLite 数据库，不会影响生产数据。

## 🤝 贡献指南

欢迎基于 PRD 提出产品迭代建议或提交代码改进。提交 PR 前请确保：

- 新增 / 修改的业务逻辑附带相应测试。
- 通过 `pytest` 并更新相关文档。
- 遵循 PRD 中的术语与业务规则描述。
