import turtle

# 創建畫布
screen = turtle.Screen()
screen.setup(500,500)
# 創建 turtle 物件
t = turtle.Turtle()
# 移動 turtle
for _ in range(4):
    t.forward(100)
    t.left(90)
# 保持視窗開啟
turtle.done()