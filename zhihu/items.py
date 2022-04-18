# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field

class UserItem(scrapy.Item):
    id = Field()  # 存放用户对象id
    name = Field()  # 存放用户对象昵称
    avatar_url = Field()  # 存放用户对象头像jpg
    headline = Field()  # 存储用户对象的签名信息
    description = Field()  # 个人成就，如用户对象是哪方面的答主
    url = Field()  # 用户的知乎主页（不完全正确，需要忽略/api/v4）
    url_token = Field()  # 用户目标路由
    gender = Field()  # 用户性别提取，1为男性
    cover_url = Field()  # 未找到该条数据
    type = Field()  # 获取最表层的type，不知道是什么数据
    badge = Field()

    answer_count = Field()
    articles_count = Field()
    commercial_question_count = Field()
    favorite_count = Field()
    favorited_count = Field()
    follower_count = Field()
    following_columns = Field()
    following_count = Field()
    pins_count = Field()
    question_count = Field()
    thank_from_count = Field()
    thank_to_count = Field()
    thanked_count = Field()
    vote_from_count = Field()
    vote_to_count = Field()
    voteup_count = Field()
    following_favlists_count = Field()
    following_question_count = Field()
    following_topic_count = Field()
    marked_answers_count = Field()
    mutual_followees_count = Field()
    hosted_live_count = Field()
    participated_live_count = Field()

    locations = Field()
    educations = Field()
    employments = Field()
