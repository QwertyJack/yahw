#encoding:utf-8

from py2neo import Graph, Node, Relationship, authenticate
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid

# 连接数据库
url = os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474')
username="neo4j"
password="lylyy"
if username and password:
    authenticate(url.strip('http://'), username, password)
graph = Graph(url + '/db/data/')

# User类
class User:
    def __init__(self, username):
        self.username = username

    # 通过username找到用户
    def find(self):
        user = graph.find_one("User", "username", self.username)
        return user

    # 注册，创建用户
    def register(self, password):
        if not self.find():
            user = Node("User", username=self.username, password=bcrypt.encrypt(password),
                        photo="",photo_thumb="",school="",nation="",birthday="",sex="")
            graph.create(user)
            return True
        else:
            return False

    # 验证用户密码
    def verify_password(self, password):
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False

    # 发布状态
    def add_post(self, text,img_name):
        user = self.find()
        post = Node(
            "Post",
            id=str(uuid.uuid4()),
            text=text,
            image=img_name,
            timestamp=timestamp(),
            date=date(),
            like_num=0
        )
        rel = Relationship(user, "Publish", post)
        graph.create(rel)

    # 添加评论
    def add_comment(self,post_id,text,reply_user=None):
        user = self.find()
        post = graph.find_one("Post", "id", post_id)
        comment=Node("Comment",
            id=str(uuid.uuid4()),
            text=text,
            date=date(),
            timestamp=timestamp(),
            reply_user=reply_user)
        graph.create_unique(Relationship(post, "Have", comment))
        graph.create_unique(Relationship(user, "Make", comment))

    # 删除状态
    def delete_post(self,post_id):
        query="""
        match (post:Post)
        where post.id={post_id}
        detach delete post
        """
        return graph.cypher.execute(query, post_id=post_id)

    # 删除评论
    def delete_comment(self,comment_id):
        query="""
        match (comment:Comment)
        where comment.id={comment_id}
        detach delete comment
        """
        return graph.cypher.execute(query, comment_id=comment_id)

    # 为状态点赞或取消点赞
    def like_post(self, post_id):
        def like_num_change(post_id,operation):
            # 点赞数发生变化
            query="""
            MATCH (post:Post)
            WHERE post.id={post_id}
            SET post.like_num=post.like_num%s1
            """%operation
            graph.cypher.execute(query, post_id=post_id)
        query="""
        match (e:User)-[r:Like]->(post:Post)
        where e.username={username} and post.id={post_id}
        return r
        """
        r=graph.cypher.execute(query, username=self.username,post_id=post_id)
        if not r:  #如果之前没有点赞，则建立关系，并且总赞数加1
            user = self.find()
            post = graph.find_one("Post", "id", post_id)
            graph.create_unique(Relationship(user, "Like", post))
            like_num_change(post_id,"+")
        else: #如果之前点过赞，则删除关系，并且总赞数减1
            query="""
            match (e:User)-[r:Like]->(post:Post)
            where e.username={username} and post.id={post_id}
            delete r
            """
            graph.cypher.execute(query, username=self.username,post_id=post_id)
            like_num_change(post_id,"-")

    # 关注某个人或取消关注
    def follow_or_not(self,username2):
        query="""
        match (user:User)-[r:Follow]->(user2:User)
        where user.username={username} and user2.username={username2}
        return r
        """
        r=graph.cypher.execute(query, username=self.username,username2=username2)
        if not r:  #如果之前没有关注，则建立关注，返回True
            user = self.find()
            user2 = graph.find_one("User", "username", username2)
            graph.create_unique(Relationship(user, "Follow", user2, timestamp=timestamp()))
        else: #如果之前有关注，则删除关注
            query="""
            match (user:User)-[r:Follow]->(user2:User)
            where user.username={username} and user2.username={username2}
            delete r
            """
            r=graph.cypher.execute(query, username=self.username,username2=username2)
   
    # 判断是否关注
    def is_follow(self,username2):
        # 判断self是否关注了username2
        query="""
        match (user:User)-[r:Follow]->(user2:User)
        where user.username={username} and user2.username={username2}
        return r
        """
        return graph.cypher.execute(query, username=self.username,username2=username2)

    # 修改个人信息
    def change_info(self,sex,birthday,school,nation):
        query = """
        MATCH (user:User)
        WHERE user.username = {username}
        SET user.sex={sex},user.birthday={birthday},user.school={school},user.nation={nation}
        """
        return graph.cypher.execute(query, username=self.username,sex=sex,birthday=birthday,school=school,nation=nation)
    
    def change_photo(self,photo,photo_thumb):
        query = """
        MATCH (user:User)
        WHERE user.username = {username}
        SET user.photo={photo},user.photo_thumb={photo_thumb}
        """
        return graph.cypher.execute(query, username=self.username,photo=photo,photo_thumb=photo_thumb)
    
    # 查找所有用户
    def search_all_friend(self,search_content):
        query="""
        MATCH (user:User)
        WHERE user.username=~".*%s.*"
        optional match (me:User)-[r:Follow]->(user)
        where me.username={username}
        return user,r
        """%search_content
        return graph.cypher.execute(query, username=self.username)

    # 查找某个用户的好友
    def search_one_friend(self,search_friend,search_content):
        query="""
        MATCH (user1:User)-[:Follow]->(user:User)
        WHERE user.username=~".*%s.*" AND user1.username={search_friend}
        OPTIONAL MATCH (me:User)-[r:Follow]->(user)
        WHERE me.username={username}
        RETURN user,r
        """%search_content
        return graph.cypher.execute(query, search_friend=search_friend,username=self.username)
    
    # 获得某个人最近的10条状态
    def get_one_recent_posts(self):
        query = """
        MATCH (user:User)-[:Publish]->(post:Post)
        WHERE user.username = {username}
        OPTIONAL MATCH (post)-[:Have]->(content:Comment)<-[:Make]-(reviewer:User)
        WITH user,post,[content,reviewer.username] as comment
        ORDER BY content.timestamp DESC
        RETURN user,post,COLLECT(comment) AS comments
        ORDER BY post.timestamp DESC LIMIT 10
        """
        return graph.cypher.execute(query, username=self.username)

    # 获得某个人最近关注的10个人
    def get_one_follow(self):
        query = """
        MATCH (user:User)-[f:Follow]->(user2:User)
        WHERE user.username = {username}
        RETURN user2.username AS username
        ORDER BY f.timestamp DESC LIMIT 10
        """
        return graph.cypher.execute(query, username=self.username)

    # 获得10个推荐好友
    def get_recommend_friends(self):
        # 根据朋友的朋友获得5个
        query="""
        MATCH (me:User)-[:Follow]->(friend:User)-[:Follow]->(ff:User)
        WHERE me.username={username} and me.username <> ff.username
        WITH me,ff,COUNT(DISTINCT friend) AS len 
        OPTIONAL MATCH (me)-[r:Follow]->(ff)
        WITH len,ff,COUNT(r)=0 AS flag
        WHERE flag
        WITH ff,len
        ORDER BY len DESC LIMIT 5
        RETURN ff.username AS username
        """
        # 根据关注数最多的获取5个
        query2="""
        MATCH (u:User)-[:Follow]->(u2:User)
        WHERE u2.username<>{username}
        WITH COUNT(DISTINCT u) AS len,u2
        OPTIONAL MATCH (me:User)-[r:Follow]->(u2)
        WHERE me.username={username}
        WITH len,u2.username AS username,COUNT(r)=0 AS flag
        WHERE flag
        WITH len,username
        ORDER BY len DESC LIMIT 5
        RETURN username
        """
        result=[]
        for name in graph.cypher.execute(query, username=self.username):
            if name.username not in result:
                result.append(name.username)
        for name in  graph.cypher.execute(query2,username=self.username):
            if name.username not in result:
                result.append(name.username)

        return result

    # 获得点赞数最多的10个状态
    def get_hot_posts(self):
        query="""
        MATCH (p:Post)
        WHERE p.date=~"%s.*"
        RETURN p AS post
        ORDER BY p.like_num DESC LIMIT 10
        """%str(date().split(" ")[0])
        return graph.cypher.execute(query)

# 得到所有状态里面10条最新的状态
def get_all_recent_posts():
    query = """
        MATCH (user:User)-[:Publish]->(post:Post)
        OPTIONAL MATCH (post)-[:Have]->(content:Comment)<-[:Make]-(reviewer:User)
        WITH user,post,[content,reviewer.username] AS comment
        ORDER BY content.timestamp DESC
        RETURN user,post,COLLECT(comment) AS comments
        ORDER BY post.timestamp DESC LIMIT 10
        """
    return graph.cypher.execute(query)

# 时间戳，用来比较各时间点的大小关系
def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

# 日期，用于时间显示
def date():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

