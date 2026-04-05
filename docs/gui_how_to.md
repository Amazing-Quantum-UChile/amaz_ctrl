

# Amazing Graphical User Interface. How to?

### 🐫 How to add a new parameter?
This is super simple: quit the GUI application, open in a text editor the `exp_param.json` file (at the root of the module) and add your parameter. Make sure you did not forget a comma and reload the GUI. It should be there!



### 🐸 How does the GUI get information (logs, points)?

#### 1. The role of servers
Before opening the graphical interface (the GUI), we launch several independent background servers. These are specialized programs that focus on one task:
* The PID Server: Its only job is to monitor and "lock" the Rb cell temperature. It works constantly to keep the hardware stable.
* The Sequence Server: This program handles the timing and execution of the experimental scripts.
* Any other server that we could need in the future.

#### 2. Communication
These servers use a tool called Pyro5 (Python Remote Objects). Instead of one big, messy program, we split the experiment into parts that "talk" to each other over a network connection. Each server sits on a specific Host (the computer's address "localhost") and a Port (a dedicated communication channel e.g. 9090, 9091...).

#### 3. Advantages of this techniques
By using this "Server-Client" structure, the system becomes much more reliable:
* Independence: The PID server can keep the temperature locked even if the GUI is closed or crashes. The "logic" is separated from the "visuals".
* Dependence: instead, we can wait one server to be ready before starting the other one. For example, if we set a new temperature for the Rb cell, the script server can wait that the temperature controller reached the target temperature before starting the temperature.
*  Remote Control: Because they use network ports, the GUI doesn't have to be on the same computer as the hardware. You can monitor the experiment from a different desk.
* Control: This setup allows the user to send commands (like "Start" or "Stop") to the servers at any time, while the servers handle the complex hardware timing in the background.




### 🐨 How to add a button?
We tried to respect the MVC (model-view-controller) which means that we split what is displayed to the user (view) to what is done in the background (model). Our graphical interface is made of a mainwindows which host a mainwidget and the mainwidget is composed of various panels e.g. a panel to diaply and modify the parameters, a panel for the pushbuttons and a panel for the log. 

Let say that you want to add button within the buttonwidget, if you look at within the code, you will see that we place button on a layout (self.layout) so that they are placed automatically. You can do it using the following
```{code}
my_new_button = QtWidgets.QPushButton("New Button")
my_new_button.setFixedHeight(self.button_height)
self.layout.addWidget(my_new_button, 1, 0, 1, 3)
self.my_new_button = my_new_button # save your button as attribute of the class
```
Then, you need to connect you button to a real action. Here, often, the action should be put in the model, which is passed as an argument and hold as attribute of any class of our GUI.
```
self.my_new_button.clicked.connect(self._model.my_new_button_pushed) 
```
and in the model.py, define the callback function. 
```
def my_new_button_pushed(self):
    """executes when the "New Button" is pushed"""
    print("I just pushed a button!!")
```

