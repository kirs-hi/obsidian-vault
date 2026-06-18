# Python 高级语法

## 浅拷贝与深拷贝

### 浅拷贝

只复制外层对象，内层嵌套对象仍然共享引用。

```python
import copy

lst = [1, 2, [3, 4]]

# 浅拷贝的三种方式
a = copy.copy(lst)
b = lst[:]
c = lst.copy()

lst[2][0] = 99
print(a)  # [1, 2, [99, 4]] —— 内层被影响
```

### 深拷贝

完全独立的副本，递归复制所有层级：

```python
import copy

lst = [1, 2, [3, 4]]
deep = copy.deepcopy(lst)

lst[2][0] = 99
print(deep)  # [1, 2, [3, 4]] —— 完全不受影响
```

### 特殊情况

不可变对象（int、str、tuple）不会真正拷贝，直接引用同一对象（因为没有修改的风险）。

```python
import copy
a = (1, 2, 3)
b = copy.copy(a)
print(a is b)  # True，同一对象
```

## 迭代器

### 可迭代对象（Iterable）

实现了 `__iter__()` 方法的对象。list、tuple、dict、str、set 都是可迭代对象。

### 迭代器（Iterator）

同时实现了 `__iter__()` 和 `__next__()` 方法的对象。

```python
from collections.abc import Iterable, Iterator

print(isinstance([1, 2], Iterable))   # True
print(isinstance([1, 2], Iterator))   # False
print(isinstance(iter([1, 2]), Iterator))  # True
```

### 使用迭代器

```python
lst = [10, 20, 30]
it = iter(lst)  # 获取迭代器

print(next(it))  # 10
print(next(it))  # 20
print(next(it))  # 30
# next(it)  # StopIteration 异常
```

`for` 循环本质上就是不断调用 `next()`，捕获 `StopIteration` 后停止。

### 自定义迭代器

```python
class CountDown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

for num in CountDown(5):
    print(num)  # 5 4 3 2 1
```

## 生成器

### 什么是生成器

带 `yield` 关键字的函数，调用时返回一个生成器对象。惰性求值，按需产生值，节省内存。

### 创建生成器

**方式一：生成器表达式**

```python
gen = (x ** 2 for x in range(10))
print(next(gen))  # 0
print(next(gen))  # 1
```

**方式二：yield 函数**

```python
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

for num in fibonacci(8):
    print(num)  # 0 1 1 2 3 5 8 13
```

### send() 方法

向生成器发送值，作为 `yield` 表达式的返回值：

```python
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value

gen = accumulator()
next(gen)          # 启动生成器，返回 0
print(gen.send(10))  # 10
print(gen.send(20))  # 30
print(gen.send(30))  # 60
```

## 命名空间

Python 有三种命名空间：

- **内置命名空间**：Python 解释器启动时创建（print、len 等）
- **全局命名空间**：模块级别定义的名称
- **局部命名空间**：函数/方法内部定义的名称

## 作用域 — LEGB 规则

变量查找顺序：**L → E → G → B**

| 层级 | 含义 | 示例 |
|------|------|------|
| L (Local) | 局部作用域 | 函数内部 |
| E (Enclosing) | 闭包外层函数 | 外层函数的局部变量 |
| G (Global) | 全局作用域 | 模块级变量 |
| B (Built-in) | 内置作用域 | print、len 等 |

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)  # local
    inner()

outer()
```

修改外层变量需要声明：

```python
def outer():
    count = 0
    def inner():
        nonlocal count  # 声明使用外层变量
        count += 1
    inner()
    print(count)  # 1
```

## 闭包

内部函数引用了外部函数的变量，且外部函数返回内部函数：

```python
def make_counter(start=0):
    count = start
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

c = make_counter()
print(c())  # 1
print(c())  # 2
print(c())  # 3

# 查看闭包绑定的变量
print(c.__closure__[0].cell_contents)  # 3
```

闭包的本质：函数 + 它引用的外部环境，形成一个封闭的整体。

## 装饰器

### 基本装饰器

本质是闭包 + 函数作为参数：

```python
def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} 耗时: {time.time() - start:.4f}s")
        return result
    return wrapper

@timer  # 等价于 slow_func = timer(slow_func)
def slow_func():
    import time
    time.sleep(1)

slow_func()
```

### 多层装饰器

从下往上装饰，从上往下执行：

```python
def bold(func):
    def wrapper():
        return f"<b>{func()}</b>"
    return wrapper

def italic(func):
    def wrapper():
        return f"<i>{func()}</i>"
    return wrapper

@bold      # 第二步装饰
@italic    # 第一步装饰
def hello():
    return "Hello"

print(hello())  # <b><i>Hello</i></b>
```

### 带参数的装饰器

需要三层嵌套：

```python
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def say_hi():
    print("Hi!")

say_hi()  # 打印 3 次 Hi!
```

### 类装饰器

通过实现 `__call__` 方法：

```python
class Logger:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        print(f"调用: {self.func.__name__}")
        return self.func(*args, **kwargs)

@Logger
def add(a, b):
    return a + b

print(add(1, 2))  # 调用: add → 3
```

---

> [!tip] 核心要点
> - 浅拷贝共享内层引用，深拷贝完全独立
> - 生成器用 yield 实现惰性求值，适合处理大数据
> - LEGB 是变量查找的核心规则
> - 装饰器 = 闭包 + 函数参数，`@` 是语法糖
