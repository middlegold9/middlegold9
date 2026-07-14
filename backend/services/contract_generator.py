"""合同生成器 —— 基于模板 + 成交数据自动生成合同草稿。

支持三类合同：二手房买卖、居间服务、资产配置顾问。
生成的是草稿，必须人工校对后再签（合规免责见文末）。
"""
from sqlalchemy.orm import Session
from datetime import datetime
import models


def _fmt_money(wan):
    """万元 → 中文展示。"""
    if not wan:
        return "0"
    return f"{wan:,.0f}万元（人民币 {wan * 10000:,.0f} 元）"


def generate_contract(db: Session, transaction_id: int, contract_type: str = "二手买卖") -> models.Contract:
    txn = db.query(models.Transaction).get(transaction_id)
    if not txn:
        raise ValueError("成交记录不存在")
    client = db.query(models.Client).get(txn.client_id) if txn.client_id else None
    prop = db.query(models.Property).get(txn.property_id) if txn.property_id else None

    today = datetime.now().strftime("%Y年%m月%d日")
    buyer = client.name if client else "____"
    prop_name = prop.name if prop else "____"
    area = prop.area if prop else "____"
    addr = f"{prop.district or ''}{prop.block or ''}{prop.name}" if prop else "____"

    if contract_type == "二手买卖":
        content = f"""深圳市存量房买卖合同（草稿）

签订日期：{today}
买方（乙方）：{buyer}
卖方（甲方）：____（待补充）

第一条 标的房屋
房屋坐落：{addr}
建筑面积：{area} 平方米
成交总价：{_fmt_money(txn.deal_price)}
单价：约 {prop.unit_price if prop else '____'} 元/平方米

第二条 价款支付
1. 定金：成交价 10%，于本合同签订之日支付；
2. 首付款：按银行评估及贷款政策执行；
3. 尾款：过户当日结清。

第三条 房屋交付
甲方应于收齐全部房款后 ___ 日内将房屋交付乙方，水电物业费结清。

第四条 税费承担
按深圳市现行规定，各自承担应缴税费（具体以税务部门核定为准）。

第五条 居间服务
本次交易由 ____（经纪机构）提供居间服务，佣金 {_fmt_money(txn.commission)}。

第六条 违约责任
任一方违约，应向守约方支付成交价 20% 作为违约金。

第七条 争议解决
协商不成的，提交房屋所在地人民法院诉讼解决。

甲方（签字）：__________  乙方（签字）：__________
"""
    elif contract_type == "居间服务":
        content = f"""房地产经纪居间服务合同（草稿）

签订日期：{today}
委托方：{buyer}
经纪方：____（经纪机构）

一、服务内容：就 {addr} 房屋提供居间撮合、协助网签、办理过户等服务。
二、成交价：{_fmt_money(txn.deal_price)}
三、佣金：{_fmt_money(txn.commission)}，于网签当日支付。
四、其他约定：____

委托方（签字）：__________  经纪方（签字）：__________
"""
    else:  # 资产配置顾问
        content = f"""资产配置顾问服务协议（草稿）

签订日期：{today}
客户：{buyer}

一、服务范围：房产投资、理财产品、保险配置、香港身份规划、子女教育规划等综合咨询。
二、服务期限：自签订之日起 12 个月。
三、顾问费：____（按资产规模协商）。
四、保密条款：顾问方对客户资产信息严格保密。
五、免责声明：本服务仅提供咨询建议，不构成投资承诺，投资有风险。

客户（签字）：__________  顾问方（签字）：__________
"""

    contract = models.Contract(
        transaction_id=transaction_id,
        client_id=txn.client_id,
        contract_type=contract_type,
        content=content,
        status="草稿",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract
