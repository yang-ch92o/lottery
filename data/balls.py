
import Box2D as box2d
import pygame
import sys, os, traceback
import random
import time
import tomllib
import secrets

join=os.path.join
dir=os.path.dirname(__file__)

class Ball:
	def __init__(
			self, world: box2d.b2World, x, y, r=1, 
			density=1,restitution=.5,friction=0.3,color=(255,0,0),**tag
		):
		self.world = world
		self.body = world.CreateDynamicBody(position=(x, y), angle=0.1)
		self.body.CreateCircleFixture(
			radius=r, density=density,restitution=restitution,friction=friction
		)
		self.position = tuple(self.body.position)
		self.r = r
		self.color = color
		if tag is None:self.tag={}
		else:self.tag=tag
	def draw(self, screen:pygame.Surface,scale=10):
		pygame.draw.circle(
			screen, self.color, 
			(self.body.position[0]*scale,self.body.position[1]*scale), self.r*scale
		)
def input_intergral(rect,max_val=10):
	inp=''
	numkeys=[pygame.K_0,pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4,pygame.K_5,pygame.K_6,pygame.K_7,pygame.K_8,pygame.K_9]
	font = pygame.font.Font(None, 32)
	scr=pygame.Surface((rect[2],rect[3]))
	while True:
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key in numkeys:
					inp+=str(numkeys.index(event.key))
					if int(inp)>max_val:
						inp=inp[:-1]
				elif event.key == pygame.K_BACKSPACE:
					inp=inp[:-1]
				elif event.key == pygame.K_RETURN:
					if inp:return int(inp)
					else:return 0
				elif event.key in {pygame.K_ESCAPE,pygame.K_q}:
					return 0
			elif event.type==pygame.QUIT:
				return 0
		scr.fill((255,255,255))
		text=font.render(inp,True,(0,0,0))
		scr.blit(text,(0,0))
		pygame.display.get_surface().blit(scr,(rect[0],rect[1]))
		pygame.display.update(rect)
def random_force(rangex=(-10000,10000),rangey=(-10000,10000)):
	for i in items:
		i.body.ApplyForce((random.randint(*rangex),random.randint(*rangey)),i.body.worldCenter,True)
message=\
'''\
[S]     Start
[F]     Shake
[R]     Reset
[O]     Open/Close Hole
[Enter] Show Winners
[Q]     Quit
'''

pygame.font.init()
pygame.init()

world = box2d.b2World((0,10))
items:list[Ball]=[]
def random_string(length=10):
	c=0
	skip=[(0xd800,0xdfff),(0,31),(0xe000,0xf8ff),(0x1780,0x1c7f),(0xfff0,0xffff),(0xfb00,0xfdff),(0xa800,0xabff),(0xac00,0xd7ff)]
	ch=''
	while c<length:
		n=random.randint(0,0xffff)
		for i in skip:
			if i[0]<=n<=i[1]:
				break
		else:
			c+=1
			ch+=chr(n)
		
	return ch
def main(gcfgf=None,cfgf=None,membercfg=None):
	class ToolbarButton:
		x:int
		w:int
		r:pygame.Rect
		cm:bool
		def __init__(self,text,func,color="#1C396C",pressed_color="#254C91"):
			self.text=text
			self.func=func
			self.color=color
			self.pressed_color=pressed_color
		def get_text(self):
			return self.text
	all_names:list[str]
	cfg:dict
	fontpath:str
	font:pygame.font.Font
	gconfig:dict
	def rf():
		random_force((-cfg['force'],cfg['force']),(-cfg['force'],cfg['force']))
	def create_new_ball(pos=None,force=None,**tags):
		if pos is None:
			w,h=pygame.display.get_surface().get_size()
			pos=(w/2+random.randint(-200,200)/3,h/2+random.randint(-200,200)/3)
		color=random.choice(cfg['dark-ball-colors']+cfg['light-ball-colors'])
		if color in cfg['dark-ball-colors']:
			fg=cfg['dark-ball-fg']
		else:
			fg=cfg['light-ball-fg']
		items.append(Ball(world,pos[0]/10,pos[1]/10,density=cfg['ball-density'],restitution=cfg['ball-restitution'],friction=cfg['ball-friction'],color=color,fg=fg,**tags))
		if force is None:
			force=(random.randint(-1000,1000),random.randint(-2000,500))
		items[-1].body.ApplyForce(force,items[-1].body.worldCenter,True)
	def init_world(*_):
		nonlocal randomforcetime,openhole,show_title,extend
		extend=0
		show_title=False
		openhole=False
		randomforcetime=0
		for i in items:
			world.DestroyBody(i.body)
		items.clear()
		n=0
		l=all_names.copy()
		random.shuffle(l)
		for i in range(len(l)):
			create_new_ball(r=cfg['ball-r'],id=n)
			n+=1
		rf()
	def load(gc:str=None,c:str=None,mc:str=None):
		if gc is None:
			gc='config.toml'
		if c is None:
			c='balls.toml'
		nonlocal all_names,cfg,fontpath,font,gconfig
		all_names=[]
		gconfig = tomllib.load(open(join(dir,gc),'rb'))
		cfg=tomllib.load(open(join(dir,c),'rb'))
		fontpath=join(dir,gconfig['font'])
		font=pygame.font.Font(fontpath,cfg['font-size'])
		if mc is None:mc='members.toml'
		v=tomllib.load(open(join(dir,mc),'rb'))
		for i in v['number']:
			if i not in v['disabled']:
				for _ in range(v['number'][i]):
					all_names.append(i)
		del v
	def shake(s:ToolbarButton=None):
		nonlocal randomforcetime
		if randomforcetime<=0:
			randomforcetime=240
		else:
			randomforcetime=0
		# if s is not None:
		# 	s.text=['停止摇晃','开始摇晃'][randomforcetime>0]

	def open_or_close_hole(s:ToolbarButton=None):
		nonlocal openhole
		openhole=not openhole
	def show_or_hide_title(s:ToolbarButton=None):
		nonlocal show_title,title
		show_title=not show_title
		if show_title:
			title=rend_title()
	def rend_title():
		if len(winners_names)==0:n=cfg['win-text']%'没有人'
		else:
			n=list(set(winners_names))
			n.sort()
			n=cfg['win-text']%(cfg['winner-sep'].join(n))
		try:
			title=titlefont.render(n,True,cfg['title-fg'],cfg['title-bg'],ws-cfg['title-edge']*2)
		except:
			traceback.print_exc()
			title=titlefont.render(n,True,cfg['title-fg'],cfg['title-bg'])
		return title
	def 掀起():
		for i in items:
			i.body.ApplyForce((0,-cfg['force']/1.5),i.body.worldCenter,True)
	load(gcfgf,cfgf,membercfg)
	uicfg={'toolbar-height':24,'toolbar-bg':"#202020"}
	os.chdir(dir)
	# print(os.getcwd())
	# print(message)
	window = pygame.display.set_mode(cfg['default-resoulution'],pygame.DOUBLEBUF|pygame.RESIZABLE)
	pygame.display.set_icon(pygame.image.load(join(dir,cfg['icon'])))
	g=world.CreateStaticBody(position=(0, 0))
	pygame.display.set_caption("Lottery - Balls")
	pygame.key.stop_text_input()
	t=0
	clock=pygame.time.Clock()
	speed=2.0
	init_world()
	randomforcetime=0
	show_title=False
	extend=0
	ballimg=[pygame.transform.scale,pygame.transform.smoothscale][int(cfg['ball-smooth'])](pygame.image.load(join(dir,cfg['ball-image'])),(cfg['ball-r']*20,cfg['ball-r']*20))
	if cfg['ball-onecolor']:
		ballimg.fill('white',None,pygame.BLEND_RGB_ADD)
	openhole=False
	show_title=False
	titlefont=pygame.font.Font(fontpath, cfg['title-font-size'])
	toolbartools=[ToolbarButton('开始摇晃',shake),ToolbarButton('重置',init_world),ToolbarButton('打开洞',open_or_close_hole),ToolbarButton('显示获奖名单',show_or_hide_title),ToolbarButton('摇晃',rf),ToolbarButton('掀起',掀起),ToolbarButton('退出',sys.exit,"#9c0000")]
	tbfont:pygame.font.Font=pygame.font.Font(fontpath,14)
	toolbartools[0].get_text=lambda:['停止摇晃','开始摇晃'][randomforcetime<=0]
	toolbartools[2].get_text=lambda:['打开洞','关闭洞'][openhole]
	winners=[]
	winners_names=[]
	if cfg['bg-img']:
		bgimg=pygame.image.load(join(dir,cfg['bg-img'])).convert()
	else:
		bgimg=None
	while True:
		ws,hs=pygame.display.get_surface().get_size()
		hs-=uicfg['toolbar-height']
		screen=pygame.Surface((ws,hs))
		w=ws/10
		h=hs/10
		randomforcetime-=1
		if randomforcetime>=0 and randomforcetime%2==0:
			rf()
			if randomforcetime==0:
				openhole=True
			# 	toolbartools[0].text='开始摇晃'
			# else:
			# 	toolbartools[0].text='停止摇晃'
		toolbarimg=pygame.Surface((ws,uicfg['toolbar-height']),)
		toolbarimg.fill(uicfg['toolbar-bg'])
		_tbx=6
		_pa=10
		for i in toolbartools:
			text=tbfont.render(i.get_text(),True,'white')
			i.x=_tbx-_pa/2
			i.w=text.get_width()+_pa
			i.r=pygame.Rect(i.x,0,i.w,uicfg['toolbar-height'])
			_tbx+=text.get_width()+_pa
			if i.r.collidepoint(pygame.mouse.get_pos()):
				i.cm=1
				toolbarimg.fill(i.pressed_color if pygame.mouse.get_pressed()[0] else i.color,i.r)
			else:
				i.cm=0
			toolbarimg.blit(text,(i.x+_pa/2-1,0))
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				match event.key:
					case pygame.K_SPACE:
						掀起()
					case pygame.K_s:
						randomforcetime=240
					case pygame.K_p:
						randomforcetime=0
					case pygame.K_f:
						random_force((-cfg['force'],cfg['force']),(-cfg['force'],cfg['force']))
					case pygame.K_r:
						init_world()
					case pygame.K_o:
						openhole=not openhole
					case pygame.K_RIGHT:
						extend+=1
					case pygame.K_LEFT:
						extend-=1
						if extend<0:extend=0
					case pygame.K_F11:
						pygame.display.toggle_fullscreen()
					case pygame.K_RETURN:
						if len(winners)>0:
							show_title=True
							title=rend_title()
							print(cfg['win-text']%(cfg['winner-sep'].join(winners_names)))
						else:
							show_title=False
					case pygame.K_q:
						sys.exit()
					case pygame.K_EQUALS:
						speed*=2
						speed=min(8192.0,speed)
					case pygame.K_MINUS:
						speed/=2
						speed=max(1/64,speed)
					# case _:
					# 	create_new_ball()
			elif event.type == pygame.MOUSEBUTTONUP:
				if event.button==pygame.BUTTON_LEFT:
					if pygame.mouse.get_pos()[1]<uicfg['toolbar-height']:
						for i in toolbartools:
							if i.cm:
								i.func()
		for i in g.fixtures:
			g.DestroyFixture(i)
		_holedepth=cfg['hole-depth']
		floor_y=cfg['floor-y']
		_space=cfg['hole-space']
		_w=cfg['ball-r']*(extend+1)
		_slopetop=-cfg['slope']*w/2+h-floor_y
		l=[
			[(0,_slopetop), (w/2-(_w+_space),h-floor_y)], # 地面左
			[(w/2+(_w+_space),h-floor_y), (w,_slopetop)], # 地面右
			[(0,-1), (w,-1)], # 天花板
			[(0,h), (0,-1)], # 左墙
			[(w,h), (w,-1)], # 右墙
			[(w/2-(_w+_space),h-floor_y), (w/2-(_w+_space),h-floor_y+_holedepth)], # 坑左墙
			[(w/2+(_w+_space),h-floor_y), (w/2+(_w+_space),h-floor_y+_holedepth)], # 坑右墙
			[(w/2-(_w+_space),h-floor_y+_holedepth), (w/2+(_w+_space),h-floor_y+_holedepth)], # 坑底
		]
		if not openhole:
			l.append([(w/2-(_w+_space),h-floor_y), (w/2+(_w+_space),h-floor_y)])

		# (255, 160, 160)
		screen.fill(cfg['bg'])  # 填充背景
		if bgimg:
			screen.blit(pygame.transform.smoothscale(bgimg,(ws,hs)),(0,0))
		# world.Step(1/60, 6, 2)
		for i in l:
			pygame.draw.line(screen,cfg['edge-color'],(i[0][0]*10+cfg['edge-offset'][0],i[0][1]*10+cfg['edge-offset'][1]),(i[1][0]*10+cfg['edge-offset'][0],i[1][1]*10+cfg['edge-offset'][1]),cfg['edge-width'])
			g.CreateEdgeFixture(vertices=i)
		winners=[]
		winners_names=[]
		for i in items:
			if cfg['ball-useimg']:
				b=ballimg.copy()
				b.fill(i.color,None,pygame.BLEND_MULT)
				screen.blit(b,(i.body.position[0]*10-cfg['ball-r']*10,i.body.position[1]*10-cfg['ball-r']*10))
			else:
				i.draw(screen,)  # 渲染场景
			match str(cfg['ball-text-type']).lower():
				case 'number':
					text=str(i.tag.get('id',-1)+1)
				case 'same':
					text=cfg['samename']
				case 'name':
					text=all_names[i.tag.get('id',0)] if cfg['floor-y'] else str(i.tag.get('id',float('nan'))+1).replace('nan','?')
				case 'random':
					text=random_string(random.randint(3,8))
				case typ:
					text=str(typ)
			try:
				f=font.render(text,cfg['ball-text-antialias'],i.tag.get('fg','#ff00ff'))
			except:
				f=pygame.Surface((1,1),pygame.SRCALPHA)
			screen.blit(f,(i.body.position[0]*10-f.get_width()/2+cfg['text-offset'][0],i.body.position[1]*10-f.get_height()/2+cfg['text-offset'][1]))

			if i.body.position[1]>(h-cfg['floor-y']):
				winners.append(i.tag.get('id',0))
				winners_names.append(all_names[i.tag.get('id',0)])
		if show_title:
			try:
				tw,th=title.get_size()
				screen.blit(title,(ws/2-tw/2+cfg['title-offset'][0],hs/2-th/2+cfg['title-offset'][1]))
			except:pass
		window.blit(screen,(0,uicfg['toolbar-height']))
		# window.fill('#121212',(0,0,ws,uicfg['toolbar-height']))
		window.blit(toolbarimg,(0,0))
		pygame.display.update()
		for _ in range(max(1,int(speed))):world.Step(1/60, 6, 2)  # 更新物理世界
		clock.tick(60*min(1,speed))  # 控制帧率
		pygame.display.set_caption("Lottery - Balls | FPS: %1.1f"%clock.get_fps())
		t+=1
if __name__=='__main__':
	import sys, argparse
	parser = argparse.ArgumentParser(description='Balls Lottery')
	parser.add_argument('-c','--config',default='balls.toml',help='config file')
	parser.add_argument('-mc','--members',default='members.toml',help='member config file')
	parser.add_argument('-gc','--globalconfig',default='config.toml',help='global config file')
	args = parser.parse_args()

	main(args.globalconfig,args.config,args.members)