import React, { useEffect, useState } from 'react'
import * as api from './api'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

const NAV = [
  { key: 'dashboard', label: '总览看板', icon: '📊' },
  { key: 'ingestion', label: '文档入库', icon: '📥' },
  { key: 'transactions', label: '二手成交', icon: '💰' },
  { key: 'intel', label: '区域情报', icon: '🗺️' },
  { key: 'auctions', label: '土拍市场', icon: '🏗️' },
  { key: 'content', label: '自媒体内容', icon: '🎬' },
  { key: 'clients', label: 'VIP客户', icon: '👤' },
  { key: 'meetings', label: '会面安排', icon: '📅' },
  { key: 'contracts', label: '合同', icon: '📄' },
  { key: 'synergy', label: '协同事件流', icon: '🔗' },
]

export default function App() {
  const [page, setPage] = useState('dashboard')
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">深圳房产工作流<br /><span>FDE 一体化协同系统</span></div>
        {NAV.map(n => (
          <div key={n.key}
            className={`nav-item ${page === n.key ? 'active' : ''}`}
            onClick={() => setPage(n.key)}>
            <span>{n.icon}</span> {n.label}
          </div>
        ))}
      </aside>
      <main className="main">
        {page === 'dashboard' && <Dashboard />}
        {page === 'ingestion' && <Ingestion />}
        {page === 'transactions' && <Transactions />}
        {page === 'intel' && <Intel />}
        {page === 'auctions' && <Auctions />}
        {page === 'content' && <Content />}
        {page === 'clients' && <Clients />}
        {page === 'meetings' && <Meetings />}
        {page === 'contracts' && <Contracts />}
        {page === 'synergy' && <Synergy />}
      </main>
    </div>
  )
}

function Title({ t, s }) {
  return <><div className="page-title">{t}</div><div className="page-sub">{s}</div></>
}

/* ---------------- 总览 ---------------- */
function Dashboard() {
  const [d, setD] = useState(null)
  const [stats, setStats] = useState(null)
  useEffect(() => {
    api.getDashboard().then(setD)
    api.getTransactionStats().then(setStats)
  }, [])
  if (!d) return <div>加载中…</div>
  const chartData = stats ? Object.entries(stats.by_district).map(([k, v]) => ({
    district: k, commission: v.commission,
  })) : []
  const colors = ['#2563eb', '#16a34a', '#d97706']
  return (
    <>
      <Title t="总览看板" s="7 大板块统一视图，左侧切换各业务模块" />
      <div className="cards">
        <Stat n={d.deal_count} l="累计成交（笔）" />
        <Stat n={`${d.total_commission}万`} l="累计佣金" cls="green" />
        <Stat n={d.vip_count} l="VIP 客户" cls="gold" />
        <Stat n={d.high_value_count} l="高净值客户" />
        <Stat n={d.auto_content_count} l="自动生成选题" cls="green" />
        <Stat n={d.synergy_event_count} l="协同事件" cls="gold" />
      </div>
      <div className="panel">
        <h3>📍 各区域佣金贡献</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData}>
            <XAxis dataKey="district" /><YAxis />
            <Tooltip formatter={(v) => `${v}万`} />
            <Bar dataKey="commission" radius={[6, 6, 0, 0]}>
              {chartData.map((e, i) => <Cell key={i} fill={colors[i % 3]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  )
}
function Stat({ n, l, cls = '' }) {
  return <div className="card"><div className={`num ${cls}`}>{n}</div><div className="label">{l}</div></div>
}

/* ---------------- 文档入库 ---------------- */
function Ingestion() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const onFile = async (e) => {
    const f = e.target.files[0]
    if (!f) return
    setLoading(true); setResult(null)
    try { setResult(await api.uploadDocument(f)) }
    catch (err) { setResult({ error: String(err) }) }
    finally { setLoading(false) }
  }
  return (
    <>
      <Title t="文档入库" s="把散落在 PDF / Word / PPT 的成交、土拍、房源数据自动结构化入库，并触发协同" />
      <div className="panel">
        <label className="upload-box" style={{ display: 'block' }}>
          {loading ? '解析中…' : '📥 点击上传 PDF / Word / PPT 文件，自动抽取数据'}
          <input type="file" accept=".pdf,.docx,.doc,.pptx,.ppt" hidden onChange={onFile} />
        </label>
        {result && (
          <div style={{ marginTop: 16 }}>
            {result.error ? <div className="intel-tip">{result.error}</div> :
              <div className="rec">
                ✅ <b>{result.filename}</b> 已入库：
                成交 {result.ingested?.transactions || 0} 笔，
                土拍 {result.ingested?.auctions || 0} 条，
                房源 {result.ingested?.properties || 0} 套
                （已自动触发协同：选题生成 / 客户评分）
              </div>}
          </div>
        )}
      </div>
      <div className="panel">
        <h3>💡 入库即协同</h3>
        <div className="rec">土拍数据入库 → 自动生成「土拍分析 / 区域解读」选题</div>
        <div className="rec">大额成交入库 → 客户自动评分升级，推入 VIP 资产配置漏斗</div>
        <div className="rec">豪宅房源入库 → 自动生成「实探看房」选题</div>
      </div>
    </>
  )
}

/* ---------------- 成交 ---------------- */
function Transactions() {
  const [list, setList] = useState([])
  useEffect(() => { api.getTransactions().then(setList) }, [])
  return (
    <>
      <Title t="二手成交" s="核心现金流板块。成交录入即触发客户价值重估" />
      <div className="panel">
        <table>
          <thead><tr><th>类型</th><th>区域</th><th>成交价</th><th>佣金</th><th>来源文档</th></tr></thead>
          <tbody>{list.map(t => (
            <tr key={t.id}>
              <td><span className="tag blue">{t.deal_type}</span></td>
              <td>{t.district}</td><td>{t.deal_price}万</td>
              <td style={{ color: '#16a34a', fontWeight: 600 }}>{t.commission}万</td>
              <td style={{ color: '#9ca3af' }}>{t.source_doc}</td>
            </tr>))}</tbody>
        </table>
      </div>
    </>
  )
}

/* ---------------- 区域情报 ---------------- */
function Intel() {
  const [cards, setCards] = useState([])
  useEffect(() => { api.getDistrictIntel().then(setCards) }, [])
  return (
    <>
      <Title t="区域情报（福田 / 南山 / 宝中）" s="聚合成交 + 在售 + 土拍数据，自动给出调价 / 选题建议" />
      <div className="cards" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(300px,1fr))' }}>
        {cards.map(c => (
          <div key={c.district} className="card intel-card">
            <div style={{ fontWeight: 700, fontSize: 16 }}>{c.district}</div>
            <div style={{ fontSize: 13, color: '#6b7280', marginTop: 8, lineHeight: 1.9 }}>
              成交 {c.deal_count} 笔 · 均价 {c.avg_deal_price}万<br />
              在售 {c.listing_count} 套 · 挂牌单价 {c.avg_listing_unit_price}元/㎡<br />
              最新土拍楼面价 {c.max_floor_price}元/㎡
            </div>
            {c.tip && <div className="intel-tip">{c.tip}</div>}
          </div>
        ))}
      </div>
    </>
  )
}

/* ---------------- 土拍 ---------------- */
function Auctions() {
  const [list, setList] = useState([])
  useEffect(() => { api.getAuctions().then(setList) }, [])
  return (
    <>
      <Title t="土拍市场" s="土拍记录入库自动生成自媒体选题" />
      <div className="panel">
        <table>
          <thead><tr><th>地块</th><th>区域</th><th>位置</th><th>楼面价</th><th>溢价率</th><th>竞得方</th></tr></thead>
          <tbody>{list.map(a => (
            <tr key={a.id}>
              <td>{a.parcel_no}</td><td>{a.district}</td><td>{a.location}</td>
              <td>{a.floor_price}元/㎡</td>
              <td style={{ color: a.premium_rate >= 15 ? '#dc2626' : '#374151' }}>{a.premium_rate}%</td>
              <td>{a.winner}</td>
            </tr>))}</tbody>
        </table>
      </div>
    </>
  )
}

/* ---------------- 内容 ---------------- */
function Content() {
  const [p, setP] = useState(null)
  useEffect(() => { api.getContentPipeline().then(setP) }, [])
  if (!p) return <div>加载中…</div>
  const cols = ['选题', '拍摄中', '已发布']
  return (
    <>
      <Title t="自媒体内容流水线" s={`共 ${p.total} 条，其中 ${p.auto_generated} 条由协同引擎自动生成`} />
      <div className="cards" style={{ gridTemplateColumns: 'repeat(3,1fr)' }}>
        {cols.map(col => (
          <div key={col} className="panel">
            <h3>{col}（{(p.pipeline[col] || []).length}）</h3>
            {(p.pipeline[col] || []).map(c => (
              <div key={c.id} className="rec">
                {c.auto && <span className="tag auto">自动</span>}
                <span className="tag blue">{c.category}</span><br />
                <span style={{ fontSize: 13 }}>{c.title}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </>
  )
}

/* ---------------- 客户 ---------------- */
function Clients() {
  const [list, setList] = useState([])
  const [sel, setSel] = useState(null)
  useEffect(() => { api.getClients().then(setList) }, [])
  const open = (id) => api.getClient360(id).then(setSel)
  const levelTag = (lv) => lv === 'VIP' ? 'vip' : lv === '高净值' ? 'high' : 'normal'
  return (
    <>
      <Title t="VIP 客户 / 资产配置" s="客户360：聚合全板块足迹 + 跨板块服务推荐" />
      <div className="panel">
        <table>
          <thead><tr><th>客户</th><th>等级</th><th>价值分</th><th>净资产</th><th>兴趣片区</th><th></th></tr></thead>
          <tbody>{list.map(c => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td><span className={`tag ${levelTag(c.level)}`}>{c.level}</span></td>
              <td><b>{c.value_score}</b></td>
              <td>{c.net_worth_estimate}万</td>
              <td>{(c.interest_districts || []).join('、')}</td>
              <td><button className="btn ghost" onClick={() => open(c.id)}>客户360</button></td>
            </tr>))}</tbody>
        </table>
      </div>
      {sel && (
        <div className="panel">
          <h3>👤 客户360 —— {sel.client.name}</h3>
          <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 12 }}>
            {sel.client.level} · 价值分 {sel.client.value_score} · 净资产 {sel.client.net_worth_estimate}万
          </div>
          <b style={{ fontSize: 13 }}>成交记录（{sel.transactions.length}）</b>
          {sel.transactions.map(t => (
            <div key={t.id} className="rec">{t.deal_type} {t.district} 成交 {t.deal_price}万（佣金 {t.commission}万）</div>
          ))}
          <b style={{ fontSize: 13 }}>跨板块协同推荐</b>
          {sel.recommendations.length ? sel.recommendations.map((r, i) => (
            <div key={i} className="rec">→ {r}</div>
          )) : <div className="rec">暂无</div>}
        </div>
      )}
    </>
  )
}

/* ---------------- 会面 ---------------- */
function Meetings() {
  const [list, setList] = useState([])
  const [brief, setBrief] = useState(null)
  useEffect(() => { api.getMeetings().then(setList) }, [])
  return (
    <>
      <Title t="VIP 客户会面" s="创建会面自动生成 brief —— 拉取该客户全板块画像" />
      <div className="panel">
        <table>
          <thead><tr><th>客户ID</th><th>时间</th><th>地点</th><th>议题</th><th>状态</th><th></th></tr></thead>
          <tbody>{list.map(m => (
            <tr key={m.id}>
              <td>{m.client_id}</td>
              <td>{m.meet_date?.slice(0, 16).replace('T', ' ')}</td>
              <td>{m.location}</td><td>{m.agenda}</td><td>{m.status}</td>
              <td><button className="btn ghost" onClick={() => api.getMeetingBrief(m.id).then(setBrief)}>查看Brief</button></td>
            </tr>))}</tbody>
        </table>
      </div>
      {brief && <div className="panel"><h3>📋 会面 Brief</h3><div className="brief">{brief.brief}</div></div>}
    </>
  )
}

/* ---------------- 合同 ---------------- */
function Contracts() {
  const [list, setList] = useState([])
  const [sel, setSel] = useState(null)
  useEffect(() => { api.getContracts().then(setList) }, [])
  return (
    <>
      <Title t="合同" s="基于成交数据自动生成草稿（需人工校对后签署）" />
      <div className="panel">
        <table>
          <thead><tr><th>ID</th><th>类型</th><th>状态</th><th></th></tr></thead>
          <tbody>{list.map(c => (
            <tr key={c.id}>
              <td>{c.id}</td><td><span className="tag blue">{c.contract_type}</span></td>
              <td>{c.status}</td>
              <td><button className="btn ghost" onClick={() => setSel(c)}>查看</button></td>
            </tr>))}</tbody>
        </table>
      </div>
      {sel && <div className="panel"><h3>📄 {sel.contract_type}</h3><div className="brief" style={{ color: '#cbd5e1' }}>{sel.content}</div></div>}
    </>
  )
}

/* ---------------- 协同事件流 ---------------- */
function Synergy() {
  const [events, setEvents] = useState([])
  useEffect(() => { api.getSynergyEvents().then(setEvents) }, [])
  return (
    <>
      <Title t="协同事件流" s="引擎自动串联 7 个板块的每一个动作（可审计）" />
      <div className="panel">
        {events.map(e => (
          <div key={e.id} className="event">
            <span className="flow">{e.source_module} → {e.target_module}</span>
            <span style={{ flex: 1 }}>
              <span className="tag blue">{e.event_type}</span> {e.description}
            </span>
            <span className="time">{e.created_at?.slice(5, 16).replace('T', ' ')}</span>
          </div>
        ))}
      </div>
    </>
  )
}
