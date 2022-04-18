import json

import scrapy
from scrapy import Spider, Request
from zhihu.items import UserItem


class ZhihusSpider(scrapy.Spider):
    name = 'zhihus'
    # allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    start_user = 'zhu-yu-long-2'
    # start_user = 'laopan233'

    # user_url是鼠标悬停时显示数据的url接口
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    # user_query是发送至user_url的载荷
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        yield Request(url=self.user_url.format(user=self.start_user, include=self.user_query), callback=self.parse_user)
        # 获取自身信息
        yield Request(url=self.follows_url.format(user=self.start_user, include=self.follows_query, offset=0, limit=20),
                      callback=self.parse_follows)
        # 获取关注列表信息
        yield Request(
            url=self.followers_url.format(user=self.start_user, include=self.followers_query, offset=0, limit=20),
            callback=self.parse_followers)
        # 获取粉丝列表信息

    def parse_user(self, response):
        result = json.loads(response.text)  # 解析响应体json
        item = UserItem()
        for field in item.fields:  # 遍历所有item
            if field in result.keys():  # 判断当前的属性如果在item的预设值中则进入
                item[field] = result.get(field)  # 向Item存入输入数据
        yield item
        yield Request(
            url=self.follows_url.format(user=result.get('url_token'), include=self.follows_query, offset=0, limit=20),
            callback=self.parse_follows)
        # 从关注列表中获取用户的url_token，即用户id，之后根据url_token、follows请求载荷、分页信息等拼接出新的follows_url，递归调用parse_follows
        yield Request(
            url=self.followers_url.format(user=result.get('url_token'), include=self.followers_query, offset=0,
                                          limit=20),
            callback=self.parse_followers)
        # 从关注列表中获取用户的url_token，即用户id，之后根据url_token、follows请求载荷、分页信息等拼接出新的follows_url，递归调用parse_follows

    def parse_follows(self, response):
        results = json.loads(response.text)  # 解析响应体json
        if 'data' in results.keys():  # 确保返回结果有data，即有关注列表
            for result in results.get('data'):  # 取出抓包followees文件中的data遍历
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)
                # 取出url_token，拼接至鼠标悬停时显示数据的url接口
                # 回调parse_user，解析用户信息
        if 'paging' in results.keys() and results.get('paging').get(
                'is_end') == False:  # 确保返回结果有paging，且paging的结果为false
            next_page = results.get('paging').get('next')  # 提取出下一页码的页面url
            yield Request(next_page, self.parse_follows)  # 提取出下一页码的url，并递归调用，一直提取出下一页的关注列表（分页访问关注列表）

    # parse_followers和parse_follows原理一致
    def parse_followers(self, response):
        results = json.loads(response.text)  # 解析响应体json
        if 'data' in results.keys():  # 确保返回结果有data，即有关注列表
            for result in results.get('data'):  # 取出抓包followees文件中的data遍历
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)
                # 取出url_token，拼接至鼠标悬停时显示数据的url接口
                # 回调parse_user，解析用户信息
        if 'paging' in results.keys() and results.get('paging').get(
                'is_end') == False:  # 确保返回结果有paging，且paging的结果为false
            next_page = results.get('paging').get('next')  # 提取出下一页码的页面url
            yield Request(next_page, self.parse_followers)  # 提取出下一页码的url，并递归调用，一直提取出下一页的关注列表（分页访问关注列表）
