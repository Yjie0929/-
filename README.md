# 知乎用户爬虫
2022已失效


---

# 前言

**补充**：这段**代码是在大学入学的第一年寒假假期写的**，现在才整理码出来的原因也只是因为看到了当初做的笔记，抽出时间想着再做一次试试能不能爬取到想要的数据，结果在测试时发现**代码已经无效**了，spider抓取不到follows，所以**只能提供一些思路上的参考**。

&emsp;&emsp;爬虫基于**Scrapy框架**实现，在**Pycharm**中编写，目的是爬取知乎用户**公开的**、**基本的信息**。该爬虫为树形结构，爬虫逻辑是通过抓包树根节点得到相关数据（关注、粉丝列表）的**fetch**文件，从该fetch的**response解析json**得到所有关注或粉丝**用户的主页URL**以及一些相关信息，将此类信息存入**Mongo**中，再通过拾取用户url为新根节点继续向下递归。

---

# 零、为什么使用Scrapy
&emsp;&emsp;Scrapy在刚学习时大家可能会认为开发过程繁琐，但在熟练地使用以后会发现Scrapy的开发效率是很高的，无论是爬取速度、反反爬技术的配置，甚至是对数据的存储也是相当方便，尤其是可以使用**CrawlSpider**做到轻轻松松爬取全站数据或全站的深度爬取。

---
# 一、开发前准备
## 1.0 emmm，需要两台有网的电脑（一台码程序，另一台看剧），一杯咖啡（提神看剧），一本书（装深沉），一个软软的枕头（看剧累了睡觉）。




---

# 二、程序主体
### 0、准备工作
创建工程：
```python
scrapy startproject zhihu
```
创建Spider：
```python
scrapy genspider zhihupc www.随便写没关系.com
```
抓包用户详细信息：
![image](https://user-images.githubusercontent.com/83082953/163723727-f7649fec-bfb7-4599-a186-838ddcd3d8c3.png)

查看用户详细信息负载，用于构建动态的user_url：
![image](https://user-images.githubusercontent.com/83082953/163723774-30474df4-259a-44b8-ae24-f6f20c0dc5a8.png)

抓包关注列表URL（粉丝列表也同理）：
![image](https://user-images.githubusercontent.com/83082953/163723811-07c711a4-03e0-476e-b8dd-8f839885929e.png)

查看关注/粉丝列表的信息（其中的url_token即用户ID）：
![image](https://user-images.githubusercontent.com/83082953/163723990-1682a23c-8d3e-437b-b479-d5142b1bb8ef.png)


### 1 配置Item类：

&emsp;&emsp;**Item类**位于项目同名文件夹下的**items.py**文件，Item类说直白点就说创建一个用于存放数据的Field对象，每个Field对象代表着不同的信息，这些数据最终都会被Pipeline持久化

#### 1.0 导包
```python
import scrapy
from scrapy import Item, Field
```
#### 1.1 Item类配置
```python
class UserItem(scrapy.Item):
    id = Field()  # 存放用户对象id
    name = Field()  # 存放用户对象昵称
    gender = Field()  # 用户性别提取，1为男性
    ...剩下想要什么自定义...
```

---
### 2、Spider配置
#### 2.0 导包
```python
import scrapy
from scrapy import Spider, Request
from zhihu.items import UserItem  # 导入Item类，静态检查会高亮或标红，无视
import json  # 这就不用多说了吧？
```
#### 2.1 Spider基本信息配置
```python
class ZhihupcSpider(scrapy.Spider):
    name = 'zhihupc'  # 爬虫名就不多说啦
	start_urls = ['http://www.zhihu.com/']  # 初始URL
	start_user = '根节点大V的用户ID'
	
	# 用户的主页URL格式化（使用user、include拼接）
	user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'  
	# user_query是发送至user_url的载荷
	user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'
	
	# 关注列表的格式化，limit是分页参数
	follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
	# follows_query是发送至follows_url的载荷
	follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
	
	# 粉丝列表的格式化，limit是分页参数
	followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
	# followers_query是发送至followers_url的载荷
	followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
```
#### 2.2 配置启动顺序，配置回调函数
```python
	# 在Spider工作后的第一事件，该方法负责抓取根节点数据
	def start_requests(self):  
		# 回调parse_user，获取根节点的信息
		yield Request(url=self.user_url.format(user=self.start_user, include=self.user_query), callback=self.parse_user)
		# 回调parse_follows，获取关注列表信息
		yield Request(url=self.follows_url.format(user=self.start_user, include=self.follows_query, offset=0, limit=20),
                      callback=self.parse_follows)
		# 回调parse_followers，获取粉丝列表信息
		yield Request(url=self.followers_url.format(user=self.start_user, include=self.followers_query, offset=0, limit=20),
            callback=self.parse_followers)
```
#### 2.3 抓取用户基本信息（parse_user）
```python
	# 该方法被调用后，解析响应的response获取用户的基本信息
	def parse_user(self, response):
		result = json.loads(response.text)  # 解析response体的json数据
		item = UserItem()  # 构造Item类
		for field in item.fields:  # 遍历所有Item类对象，.fields可以获取UserItem里所有的item
			if field in result.keys():  # 判断当前的属性如果在item的预设值中则进入
				item[field] = result.get(field)  # 向UserItem存入数据
		yield item 
		# 回调parse_follows，获取当前用户的关注列表的用户信息
		yield Request(url=self.follows_url.format(user=result.get('url_token'), include=self.follows_query, offset=0, limit=20),
            callback=self.parse_follows)
        # 回调parse_followers，获取当前用户的粉丝列表的用户信息
        yield Request(url=self.followers_url.format(user=result.get('url_token'), include=self.followers_query, offset=0,limit=20),
            callback=self.parse_followers)
```
#### 2.4 获取关注列表信息（parse_follows）
```python
	# 该方法用于解析关注列表的信息
	def parse_follows(self, response):
		results = json.loads(response.text)  # 解析response体的json数据
		if 'data' in results.keys():  # 确保返回结果有data（关注列表的数据）
			for result in results.get('data'):  # 取出抓到followees文件中的data遍历
				# 取出url_token，回调parse_user解析用户信息
				yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),self.parse_user)
		if 'paging' in results.keys() and results.get('paging').get('is_end') == False:  # 确保返回结果有paging（分页数据），且paging的结果为false
			next_page = results.get('paging').get('next')  # 提取出下一页码的页面url
			yield Request(next_page, self.parse_follows)  # 递归，一直提取出下一页的关注列表（分页访问关注列表）
```
#### 2.5 获取粉丝列表信息（parse_followers）
&emsp;&emsp;这里的**结构与parse_follows相同**，但**不建议融合**在一起，虽然空间复杂度降低了，但各功能间的**耦合度也会随之提高**，现在前后端都分离了，两个函数贴这么近做什么。
```python
	def parse_followers(self, response):
		results = json.loads(response.text)
		if 'data' in results.keys():
			for result in results.get('data'):
				yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),self.parse_user)
		if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
			next_page = results.get('paging').get('next')
			yield Request(next_page, self.parse_followers)
```

---
### 3 Pipeline配置
&emsp;&emsp;**pipeline类**位于项目同名文件夹下的**pipelines.py文件**内，该项目采用mongo存储数据，如果向更换的话也都ok，无论是mysql或是redis。

#### 3.0 导包：
```python
import pymongo  # mongo数据库
from itemadapter import ItemAdapter
```
#### 3.1 MongoPipeline类配置
因为每个人采用的存储数据的数据库不同，所以这里就不说明了吧。
```python
class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
    	# update实现去重，True表示根据前置条件查找，如果查到了就更新，没查到就去重
        self.db['user'].update({'url_token': item['url_token']}, {'&set': item},True)  
        collection_name = item.__class__.__name__
        self.db[collection_name].insert_one(ItemAdapter(item).asdict())
        return item
```
### 4 Setting配置
&emsp;&emsp;目标文件是项目同名文件夹下的**settings.py**，在这可以配置UA伪装、中间件启用、ITEM类启用等

#### 4.0 取消UA伪装注释：
```python
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html...,*/*;q=0.8',
    'Accept-Language': 'en',
    'User-Agent': 'Mozill...ari/537.36'
}
```
#### 4.1 取消遵循Robots协议：
```python
ROBOTSTXT_OBEY = False
```
#### 4.2配置控制台输出参数（只输出错误数据）：
```python
LOG_LEVEL = 'ERROR'
```
#### 4.3 启用Item类：
```python
ITEM_PIPELINES = {
    'zhihu.pipelines.MongoPipeline': 300,
}
```
#### 4.4 配置、启用Mongo（其它数据库自己看着办咯）：
```python
MONGO_URL = 'localhost'
MONGO_DATABASE = 'zhihu'
```

# 总结

&emsp;&emsp;总结...？不知道应该怎么做总结，这只爬虫是偶尔在网上看到后跟着学习的，也算是我第一次用scrapy写的爬虫吧，整理完成后，也就是今天，已经过去几年了，还有点怀念。

&emsp;&emsp;在使用scrapy前也没有接触过任何的爬虫框架，都是直接用requests发送和解析的数据，很多设置也都比较麻烦基本都手打，尤其是需要存储数据和深度爬取网站时更加苦不堪言...好在scrapy在这方面都做的比较好，虽然前期学习时感觉繁琐，但习惯后真的觉得scrapy很舒服。
