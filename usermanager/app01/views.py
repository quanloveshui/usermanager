from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.decorators import csrf
import json
import requests
import re
import os
from app01.models import *
from django.contrib.sessions.backends.db import SessionStore
from django import views
from django.utils.decorators import method_decorator
import json
from django.utils.safestring import mark_safe

#CBV方式
class Login(views.View):

    def get(self,request,*args,**kwargs):
        return render(request, 'login.html', {'msg': ''})

    def post(self, request, *args, **kwargs):
        user = request.POST.get('user')
        pwd = request.POST.get('pwd')
        num = Administrator.objects.filter(username=user, password=pwd).count()
        if num:
            request.session['is_login'] = True
            request.session['username'] = user
            rep = redirect('/index')
            return rep
        else:
            message = '用户或密码错误'
            return render(request, 'login.html', {'msg': message})




def login(request):
    message = ''
    #print(request.COOKIES)
    #v = request.session
    #print(request.session)
    #print(request.session.keys())
    #request.session.clear()
    if request.method == "POST":
        print(request.POST)
        user = request.POST.get('user')
        pwd = request.POST.get('pwd')
        '''if user == 'root' and pwd == '123':
            rep = redirect('/index')
            # 将username写入浏览器cookie，失效时间为60s
            rep.set_cookie('username',user,60)
            return rep'''
        #从数据库中查询用户和密码是否正确
        num=Administrator.objects.filter(username=user,password=pwd).count()

        if num:
            rep = redirect('/index')
            #rep.set_cookie('username', user, 60)
            request.session['is_login'] = True
            request.session['username'] = user
            return rep
        else:
            message = '用户或密码错误'
    return render(request, 'login.html',{'msg':message})


def logout(request):
    request.session.clear()
    return redirect('/login')

def auth(func):
    def inner(request, *args, **kwargs):
        is_login = request.session.get('is_login')
        if is_login:
            return func(request, *args, **kwargs)
        else:
            return redirect('/login')
    return inner

"""def index(request):
    #如果用户已经登录获取用户，否则返回登录页面,禁止用户直接访问index页面
    # 通过cookie判断用户是否已登录,提取浏览器中的cookie，如果不为空，表示已经登录
    #user = request.COOKIES.get('username')
    user = request.session.get('username')
    if user:
        return render(request,'index.html',{'user':user})
    else:
        return redirect('/login')"""

@auth
def index(request):
    current_user = request.session.get('username')
    #return render(request, 'index.html',{'user': current_user})
    return render(request, 'base.html', {'username': current_user})
#执行index函数即index()  因index函数经过装饰器装饰过的函数，index=auth(index)

@auth
def handle_classes(request):
    if request.method == "GET":
        """
        #返回所有色数据
        current_user = request.session.get('username')
        #从数据库中获取信息
        cls_list = Classes.objects.all()
        return render(request, 'classes.html', {'username': current_user,'cls_list': cls_list})
        """

        """
        '''初步实现分页功能
        10:每页显示10条数据
        current_page:当前页页码
        start：起始页码
        end: 结束页码
        cls_list：从数据库中获取的部分数据
        total_count：数据库中总数
        v:总页数
        pager_list:存放处理后带html代码(一些a标签)列表
        '''

        #第一次请求p=1
        current_page = request.GET.get('p', 1)
        current_page = int(current_page)
        # current_page       start     end
        # 1,                 0,         10
        # 2,                 10,        20
        # 3,                 20,        30
        
        start = (current_page - 1) * 10
        end = current_page * 10
        cls_list = Classes.objects.all()[start:end]
        total_count = Classes.objects.all().count()
        pager_list = []
        #计算一共多少页 v表示总页数
        v, a = divmod(total_count, 10)
        if a != 0:
            v += 1
        pager_list.append('<a href="/classes?p=%s">上一页</a>' % (current_page - 1,))
        for i in range(1,v+1):
            if i == current_page:
                #为当前页加acative样式
                pager_list.append('<a class="pageactive" href="/classes?p=%s">%s</a>' % (i, i,))
            else:
                pager_list.append('<a href="/classes?p=%s">%s</a>' % (i, i,))
        pager_list.append('<a href="/classes?p=%s">下一页</a>' % (current_page + 1,))
        pager = "".join(pager_list)
        # mark_safe(pager)
        #print(pager)
        """

        #封装类的方式实现分页
        from utils.page import PagerHelper
        current_page = request.GET.get('p', 1)
        current_page = int(current_page)
        total_count = Classes.objects.all().count()
        obj = PagerHelper(total_count, current_page, '/classes',10)
        cls_list = Classes.objects.all()[obj.db_start:obj.db_end]
        pager = obj.pager_str()
        current_user = request.session.get('username')
        return render(request,
                  'classes.html',
                  {'username': current_user, 'cls_list': cls_list, 'str_pager': pager})

    # 处理前端通过ajax方式提交过来数据
    elif request.method == "POST":
        #设置字典存放信息，传送到前端，前端根据返回信息不同做相应处理
        response_dict = {'status': True, 'error': None, 'data': None}
        caption_name = request.POST.get('caption', None)
        if caption_name:
            obj = Classes.objects.create(caption=caption_name) #obj 是一个类Classes object (5)， obj.id是添加后自增id ，obj.caption是班级名称
            #print(obj.id,obj.caption)
            response_dict['data'] = {"id": obj.id, "caption": obj.caption}

        else:
            response_dict['status'] = False
            response_dict['error'] = "标题不能为空"
        return HttpResponse(json.dumps(response_dict))

#添加班级数据，处理通过新的页面添加班级信息提交过来的数据
@auth
def handle_add_classes(request):
    message = ""
    if request.method == "GET":
        return render(request,"add_classes.html",{'msg':message})
    elif request.method == "POST":
        caption = request.POST.get("caption",None)
        if caption:
            Classes.objects.create(caption=caption)
        else:
            message = "标题不能为空"
            return render(request, "add_classes.html", {'msg': message})
        return redirect("/classes")
    else:
        return redirect("/index")

#编辑班级数据
@auth
def handle_edit_classes(request):
    if request.method == "GET":
        nid = request.GET.get('nid')
        obj = Classes.objects.filter(id=nid).first()
        return render(request,"edit_classes.html",{'obj':obj})
    elif request.method == "POST":
        nid = request.POST.get('nid')
        caption = request.POST.get('caption')
        Classes.objects.filter(id=nid).update(caption=caption)
        return redirect('/classes')
    else:
        return redirect("index")

#查询学生信息
@auth
def handle_student(request):
    if request.method == "GET":
        # for i in range(1,100):
        #     Student.objects.create(name='root' + str(i),
        #                          email='root@live.com' + str(i),
        #                          cls_id=i)
        username = request.session.get("username")
        # 封装类的方式实现分页
        from utils.page import PagerHelper
        current_page = request.GET.get('p', 1)
        current_page = int(current_page)
        total_count = Student.objects.all().count()
        obj = PagerHelper(total_count, current_page, '/student', 10)
        result = Student.objects.all()[obj.db_start:obj.db_end]
        pager = obj.pager_str()
        return render(request,'student.html',{'username':username,'result': result,'str_pager': pager})

#添加学生信息
@auth
def handle_add_student(request):
    if request.method == "GET":
        cls_list = Classes.objects.all()[0: 10]
        #print(cls_list)
        return render(request,'add_student.html',{'cls_list': cls_list})
    elif request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        cls_id = request.POST.get('cls_id')
        #print(cls_id)
        Student.objects.create(name=name,email=email,cls_id=cls_id)
        return redirect('/student')


#编辑学生信息
@auth
def handle_edit_student(request):
    if request.method == "GET":
        cls_list = Classes.objects.all()[0: 20]
        nid = request.GET.get('nid')
        obj = Student.objects.get(id=nid)
        return render(request, 'edit_student.html', {'cls_list': cls_list, "obj": obj})
    elif request.method == "POST":
        nid = request.POST.get('id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        cls_id = request.POST.get('cls_id')
        Student.objects.filter(id=nid).update(name=name, email=email, cls_id=cls_id)
        return redirect('/student')


def handle_teacher(request):
    is_login = request.session.get('is_login')
    if is_login:
        current_user = request.session.get('username')
        return render(request, 'teacher.html', {'username': current_user})
    else:
        return redirect('/login')

