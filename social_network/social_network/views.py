#encoding:utf-8

from flask import Markup, jsonify
from models import User, get_all_recent_posts
from flask import Flask, request, session, redirect, url_for, render_template, flash
import uuid
from PIL import Image

app = Flask(__name__)
# from flask import Blueprint
# app = Blueprint('app1', __name__)

# 辅助函数
def add_comment(username,post_id,text):
    if text[0]=="@":
        tem=text.find(":")
        if tem!=-1:
            reply_user=text[1:tem]
            if User(reply_user).find():
                if not text[tem+1:]: #如果回复内容为空，那么直接返回
                    return
                User(username).add_comment(post_id,text[tem+1:],reply_user)
                return
    User(username).add_comment(post_id,text)

def gen_index(username):
    recommend_friends=User(username).get_recommend_friends()
    posts = get_all_recent_posts()
    hot_posts=User(username).get_hot_posts()
    return render_template('index.html', posts=posts,recommend_friends=recommend_friends,hot_posts=hot_posts)

# 首页
@app.route('/', methods=['GET','POST'])
def index():
    # check if user valid
    if not session or not session["username"]:
        return redirect('/login')

    username = session["username"]

    # add a comment
    if request.args.get('action') == "comment":
        text = request.form["text"]
        post_id = request.form.get("post_id")
        add_comment(username, post_id, text)

    # delete a comment
    if request.args.get('action') == "dc":
        comment_id = request.args.get('cid')
        User(username).delete_comment(comment_id)

    # add a post
    if request.args.get('action') == "add":
        text = request.form['text']
        img = request.files['imgfile']
        
        if img:  #如果有图片
            img_name=str(uuid.uuid4())+".jpg"
            img.save("social_network/static/Media/"+img_name)

        if not text and not img:
            flash('不能发布空内容。'.decode("utf-8"))
        else:
            User(session['username']).add_post(text, img_name)
    
    # delete a post
    if request.args.get('action') == "delete":
        post_id = request.args.get('pid')
        User(username).delete_post(post_id)

    # like a post
    if request.args.get('action') == "like":
        post_id = request.args.get('pid')
        User(username).like_post(post_id)

    return gen_index(username)
            
# 注册
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # POST for new register
    username = request.form['username']
    password = request.form['password']
    password_confirm = request.form['password_confirm']

    if len(username) < 1:
        flash('用户名不能为空'.decode("utf-8"))
    elif ":" in username:
        flash('用户名中不能包含:'.decode("utf-8"))
    elif len(password) < 5:
        flash('密码至少包含5个字符'.decode("utf-8"))
    elif password!=password_confirm:
        flash('确认两次输入的密码一致'.decode("utf-8"))
    elif not User(username).register(password):
        flash("用户名已存在".decode("utf-8"))
    else:
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html',username=username,password=password,password_confirm=password_confirm)

# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST for login
    username = request.form['username']
    password = request.form['password']
    if not User(username).verify_password(password):
        flash('登录失败'.decode("utf-8"))
    else:
        session['username'] = username
        session['photo']=User(username).find()["photo"]
        return redirect(url_for('index'))

# 退出
@app.route('/logout')
def logout():
    # session.pop('username', None)
    session["username"]=''
    flash('退出登陆'.decode("utf-8"))
    return redirect(url_for('login'))

# deprecated !
# 添加post
@app.route('/add_post', methods=['POST'])
def add_post():
    text = request.form['text']
    img = request.files['imgfile']
    print img.filename
    img_name=""
    if img:  #如果有图片
        img_name=str(uuid.uuid4())+".jpg"
        img.save("social_network/static/Media/"+img_name)

    if not text and not img:
        flash('不能发布空内容。'.decode("utf-8"))
    else:
        User(session['username']).add_post(text,img_name)
    #return redirect(url_for('index'))
    return gen_index(session['username'])
    #return jsonify({'ret': 'ok'});

# deprecated
# 删除post
@app.route('/delete_post/<post_id>')
def delete_post(post_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    User(username).delete_post(post_id)
    return redirect(request.referrer)

# 添加comment
@app.route('/comment/<post_id>')
def comment(post_id):
    username=session["username"]
    text=request.form["text"]
    User(username).add_comment(post_id,text)
    return redirect(url)

# 删除comment
@app.route('/delete_comment/<comment_id>')
def delete_comment(comment_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    User(username).delete_comment(comment_id)
    return redirect(request.referrer)

# deprecated
# 点赞或者取消点赞
@app.route('/like_post/<post_id>')
def like_post(post_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    User(username).like_post(post_id)
    return redirect(request.referrer) 

# 关注或者取消关注
@app.route('/follow_or_not/<username2>')
def follow_or_not(username2):
    if not session:
        return render_template('login.html')
    if not session["username"]:
        return render_template('login.html')
    else:
        username = session.get('username')
        User(username).follow_or_not(username2)
        return redirect(request.referrer)

# 个人主页
@app.route('/mypage',methods=["GET","POST"])
def mypage():
    if not session or not session["username"]:
        return render_template('login.html')
    else: 
        username=session["username"]
        if request.method=="POST":
            text=request.form["text"]
            post_id=request.form.get("post_id")
            add_comment(username,post_id,text)     
        posts = User(username).get_one_recent_posts()
        follows=User(username).get_one_follow()
        user=User(username).find()
        return render_template("mypage.html",posts=posts,follows=follows,user=user)

# 好友主页
@app.route('/hispage/<username>',methods=["GET","POST"])
def hispage(username):
    if not session or not session["username"]:
        return render_template('login.html')
    else: 
        me=session["username"]
        if request.method=="POST":
            text=request.form["text"]
            post_id=request.form.get("post_id")
            add_comment(me,post_id,text)
        is_follow=User(me).is_follow(username)
        user=User(username).find()
        posts = User(username).get_one_recent_posts()
        follows=User(username).get_one_follow()
        return render_template("hispage.html",is_follow=is_follow,user=user,posts=posts,follows=follows)

# 修改个人信息
@app.route('/change_info',methods=['GET','POST'])
def change_info():
    if not session:
        return render_template('login.html')
    if not session["username"]:
        return render_template('login.html')
    else: 
        username=session["username"]
        if request.method=="POST":     #提交修改信息之后
            sex = request.form.get("sex","")
            year,month,day = request.form.get("year",""),request.form.get("month",""),request.form.get("day","")
            birthday = str(year)+"年"+str(month)+"月"+str(day)+"日"
            school = request.form.get("school","")
            nation = request.form.get("nation","")
            User(username).change_info(sex,birthday,school,nation)
            return redirect(url_for('mypage'))
        else:                           #修改信息界面
            user=User(username).find()
            return render_template("change_info.html",user=user)

# 查找关注，包括查找我的关注，查找他的关注，以及查找所有用户
@app.route('/search_friend/<search_friend>',methods=["GET","POST"])
def search_friend(search_friend):
    if not session:
        return render_template('login.html')
    if not session["username"]:
        return render_template('login.html')
    username=session["username"]
    if  not search_friend and not session["search_friend"]:
        return render_template('login.html')
    if not search_friend:
        search_friend=session["search_friend"]
    search_content=request.form.get('search_content',"")
    if search_friend=="ALL:":     #搜索所有的好友
        friends=User(username).search_all_friend(search_content)
    else:
        friends=User(username).search_one_friend(search_friend,search_content)
    session["search_friend"]=search_friend
    return render_template("search_friend.html",friends=friends)

# 修改头像
@app.route('/change_photo',methods=["GET","POST"])
def change_photo():
    if not session:
        return render_template('login.html')
    if not session["username"]:
        return render_template('login.html')

    if request.method == 'POST':
        username=session["username"]
        photo=request.files.get('imgfile',None)
        if photo:  #如果有图片
            photo_name=username+".jpg"
            photo_thumb_name=username+"_thumb"+".jpg"
            photo.save("social_network/static/Media/"+photo_name)
            img=Image.open("social_network/static/Media/"+photo_name)
            img.thumbnail((100,100))
            img.save("social_network/static/Media/"+photo_thumb_name)
            User(username).change_photo(photo_name,photo_thumb_name)
        return redirect(url_for('mypage'))
    return render_template('change_photo.html')

