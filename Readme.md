# 宁稳网(旧富投网)、集思录可转债数据&策略分析

<p align=center>
<img src="https://img.shields.io/static/v1?label=&message=docs%20%26%20demos&color=1e8a7a" alt="Docs & Demos"></a
>
<img
    alt="visitor badge"
    src="https://visitor-badge.glitch.me/badge?page_id=convertible-bond-crawler"
  />
</p>

## 数据爬取

### 入手

- 直接使用请求 HTMl 的 Response 数据覆盖 output.html 即可

- 使用 cookie 登录，直接 copy 请求头的 cookie 字段值覆盖`.env`的`login_cookie`即可

注意!!!: 建议使用[全表](https://www.ninwin.cn/index.php?m=cb&a=cb_all&show_cb_only=Y&show_listed_only=Y)页面数据，全表页面数据丰富，但全表页面需要有账号登录，注册还要考试，挺麻烦的。为了快速运行起来，可使用[简表](https://www.ninwin.cn/index.php?m=cb&show_cb_only=Y&show_listed_only=Y)页面数据

### 数据示例

![screenshot2](./screenshots/screenshot2.jpg)

### 数据参考

可跳转：[可转债全表数据](https://www.ninwin.cn/index.php?m=cb&a=cb_all)

如图
![screenshot1](./screenshots/screenshot1.jpg)

### 数据输出

提供两种输出方式：

- excel 调用 `output_excel`
- 入库到 mysql 中`store_database`

## 策略

详细文章可看[谈谈自己的可转债策略](./docs//%E8%B0%88%E8%B0%88%E8%87%AA%E5%B7%B1%E7%9A%84%E5%8F%AF%E8%BD%AC%E5%80%BA%E7%AD%96%E7%95%A5.md)

### 整体估值

参考: [集思录转债等权指数](https://www.jisilu.cn/data/cbnew/cb_index/)

可转债四象限区分

![bond_quadrant](./screenshots/bond_quadrant.png)

- 一象限：高价格，高溢价率，债性弱，股性强，收益高，风险大。

- 二象限：低价格，高溢价率，债性强，股性弱，收益低，风险小，易触发「转股价下修条款」。

- 三象限：低价格，低溢价率（双低），债性强，股性强，收益高，风险小。

- 四象限：高价格，低溢价率，债性弱，容易强赎，跟正股程度高。

> 摊大饼策略集中在第二第三象限内

### 到期保本

#### 必须条件

- 税后到期收益率 > 0 — 保本
- 距离转股时间已到 — 这样正股上涨才带得动
- 转股价格/每股净资产 > 1.5 — 下修有空间
- 满足下修条件，且不在承诺不下修时间内 — 排除那些在截至时间内承诺不下修的可转债

#### 附加条件

- 除了科创板
- 转债剩余/市值比例 > 10 — 还债压力大，下修动力强

#### 排序

- 到期收益率降序

#### 优先

- 到期收益
- 可转债价格
- 回售时间短

#### 策略结果截图

![due_result](./screenshots/due_result.jpg)

---

### 回售摸彩

#### 必须条件

- 回售内 — 回售期内
- 转股价格/每股净资产 > 1.5 — 下修有空间
- 转债剩余/市值比例 > 10 — 还债压力大，下修动力强
- 转债价格低于 115 > 有一定的安全保底
- 满足下修条件，且距离不下修承诺截止日小于一个月 — 截至时间有下修机会

#### 附件条件

- 到期时间少于半年 — 时间太短，没什么波动了
- 到期收益率> -10% — 这一约束意义不大，因为已经在转债价格有约束了

#### 排序

- 转债剩余/市值比例倒序排序

#### 策略结果截图

![return_result](./screenshots/return_result.jpg)

### 低价格低溢价

#### 条件

- 转股溢价< 10% — 低溢价
- 转债价格低于 130 — 高于 130，股性太强
- 距离转股时间—已到 — 正股上涨的话，可以及时跟上这股风
- 转股价格/每股净资产 > 1 — 有下修空间
- 距离回售时间 -- 有权, 无强赎

#### 策略结果截图

![double_low_result](./screenshots/double_low_result.jpg)

以上策略条件分别实现在以`filter_xxx`开头的函数中,例如:

```python
def filter_profit_due(df):
    df_filter = df.loc[(df['rate_expire'] > 0)
                       & (df['price'] < 115)
                       & (df['date_convert_distance'] == '已到')
                       & (df['cb_to_pb'] > 1.5)
                       & (df['is_repair_flag'] == True)
                       & (df['remain_to_cap'] > 10)
                       ]

    def my_filter(row):
        if '暂不行使下修权利' in row.repair_flag_remark or '距离不下修承诺' in row.repair_flag_remark:
            return False
        return True
    df_filter = df_filter[df_filter.apply(my_filter, axis=1)]
    output_excel(df_filter, sheet_name="到期保本")
```

### 模拟盘

按照三大策略,每周复盘一次,检查入队,出队标的. 做好跟进, 相关 json 数据,文件在`check_make.py`的中

如图:
![check](./screenshots/check.jpg)

### TODO

- 企业负债率维度
- 企业性质维度

### ChangeLog

- 2023-01-14: 修改到期保本策略条件（去掉 115 价格限制，到期收益率改为税后到期收益率）, 低价格低溢价的 cb_to_pb 改为大于 1

## 最后

如果遇到感兴趣该项目,欢迎扫描下方微信二维码（anchor_data）,欢迎交流

<img width=480  src="./screenshots/qrcode_merge.png" />
