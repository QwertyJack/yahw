
---------------------------  备注 -----------------------------

不允许转发。
上传的图片都保存在Media当中，与图片有关的都是指图片名称，地址是前面加 Media 的路径。没有图片的默认为空。


--------------------------- 数据结构 ---------------------------
                        节点  关系  属性
节点
    User
        username    唯一的标志
        password
        photo
        photo_thumb
        school
        nation
        sex
        birthday
    Post
        id          唯一的标志
        text
        image
        timestamp
        date
        like_num
    Comment
        id          唯一的标志
        text      
        date  
        timestamp
        reply_user      //回复的用户username，若不是回复则该项为空

关系
    Follow       User -> User      用户关注用户
        timestamp
    Like         User -> Post      用户点赞状态
    Publish      User ->  Post     用户发布状态
    Make         User ->  Comment  用户制作评论
    Have         Post ->  Comment  状态拥有评论

--------------------------- 使用方法 -----------------------------

a)  首先安装python2.7,并配置好环境变量以及pip工具；
b)  安装neo4j数据库2.3.0-M03,设置好密码；修改social_network/models.py中的用户名和密码；打开启动neo4j；
c)  pip install –r requirements.txt安装程序所需外置包；
d)  python run.py 启动程序；
e)  在浏览器中输入localhost:5000访问网站。















