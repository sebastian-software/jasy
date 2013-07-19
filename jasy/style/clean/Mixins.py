

def process(tree):
    __process(tree)




def __process(node):
    for child in reversed(node):
        if child is not None:
            __process(child)


    if child.type == "call":
        print("Call found: ")
        print(child)



def __finder(node, name):
    """
    Reverse scanning loop-engine for figuring out first position of given mixin
    """



