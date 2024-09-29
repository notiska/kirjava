# kirjava

![](https://raw.githubusercontent.com/notiska/kirjava/main/kirjava.png)
Artwork by [Lou](https://www.instagram.com/devils_destination/).

A Java bytecode library for Python, with decent resilience to obfuscation.  

**Warning: `dev` branch rewrite currently in beta, the entire API is subject to change.**  
Note: this is *very much* a hobby project, the maintenance schedule will fluctuate a lot. If you have any bug fixes, PRs are welcome.

## Quickstart

For more usage, see [examples](https://github.com/notiska/kirjava/tree/main/examples/).

### Installing

`python>=3.10` is required, any other versions are untested.  

You can install this library by either:
 1. Installing via pip: `pip3 install kirjava-jvm`.
 2. Cloning this repository and installing it manually:  
    - `git clone https://github.com/notiska/kirjava.git kirjava`
    - `cd kirjava`
    - `pip install .`

### Getting started

Simply import kirjava, no extra steps are required once installed:

```python3
In [1]: import kirjava
```

### Reading classfiles

kirjava contains quite a few shortcuts for various tedious tasks, an example:

```python3
In [2]: cf = kirjava.load("Test.class")

In [3]: cf
Out[3]: <ClassFile(name='Test') at 7fc10a2245c0>
```

This is *roughly equivalent* to:

```python3
In [2]: with open("Test.class", "rb") as stream:
   ...:     cf = kirjava.ClassFile.read(stream)
   ...: 

In [3]: cf
Out[3]: <ClassFile(name='Test') at 7fc10a2245c0>
```

Whatever you choose to use is up to you.  
The latter is likely more performant than the former, but if you just wish to inspect a classfile in an interactive shell, the shortcut is always available for use.

### Inspecting the class

Viewing all the methods in the class can be done via:

```python3
In [4]: cf.methods
Out[4]: 
(<MethodInfo(name='main', argument_types=(java/lang/String[],), return_type=void) at 7fc10a069a80>,
 <MethodInfo(name='<init>', argument_types=(), return_type=void) at 7fc10a0698a0>,
 <MethodInfo(name='test', argument_types=(boolean,), return_type=void) at 7fc10a069ae0>,
 <MethodInfo(name='test2', argument_types=(), return_type=void) at 7fc10a069ba0>)
```

And similarly, the fields:

```python3
In [5]: cf.fields
Out[5]: (<FieldInfo(name='field', type=int) at 7fc10a069b40>,)
```

The same goes for attributes, although this example file does not contain any:

```python3
In [6]: cf.attributes
Out[6]: {}
```

### Editing bytecode

Creating valid bytecode can be quite an annoyance, so kirjava provides functionality that allows you to edit methods with ease.  
The main classes you'll be using for this are `InsnGraph`, `InsnBlock` and `InsnEdge`.

#### Disassembly

To disassemble a method, you can use the shortcut:

```python3
In [7]: graph = kirjava.disassemble(cf.get_method("test"))

In [8]: graph
Out[8]: <InsnGraph(blocks=10, edges=12) at 7fc10abfed50>
```

Or more verbosely:

```python3
In [7]: graph = kirjava.analysis.InsnGraph.disassemble(cf.get_method("test"))

In [8]: graph
Out[8]: <InsnGraph(blocks=10, edges=12) at 7fc10abfed50>
```

You can then view the blocks and edges present in the graph:

```python3
In [9]: graph.blocks
Out[9]: 
(<InsnBlock(label=0, instructions=[iload_1]) at 7fc10a1ed340>,
 <InsnReturnBlock() at 7fc10b60e5d0>,
 <InsnRethrowBlock() at 7fc10ab8f5c0>,
 <InsnBlock(label=1, instructions=[aload_0, iconst_0, putfield Test.field:I]) at 7fc10abc9f80>,
 <InsnBlock(label=2, instructions=[aload_0, getfield Test.field:I]) at 7fc10abcac40>,
 <InsnBlock(label=3, instructions=[iconst_0]) at 7fc10a2138c0>,
 <InsnBlock(label=4, instructions=[]) at 7fc10a211f00>,
 <InsnBlock(label=5, instructions=[iload_1]) at 7fc10a210340>,
 <InsnBlock(label=6, instructions=[]) at 7fc10a2103c0>,
 <InsnBlock(label=7, instructions=[iinc 1 by 1]) at 7fc10a213240>)

In [10]: graph.edges
Out[10]: 
(<FallthroughEdge(from=block 0, to=block 1)>,
 <JumpEdge(from=block 0, to=block 2, instruction=ifne)>,
 <FallthroughEdge(from=block 1, to=block 2)>,
 <FallthroughEdge(from=block 2, to=block 3)>,
 <JumpEdge(from=block 2, to=block 4, instruction=ifgt)>,
 <JumpEdge(from=block 3, to=block 5, instruction=ifeq)>,
 <FallthroughEdge(from=block 3, to=block 4)>,
 <JumpEdge(from=block 4, to=return block, instruction=return)>,
 <FallthroughEdge(from=block 5, to=block 6)>,
 <JumpEdge(from=block 5, to=block 7, instruction=ifeq)>,
 <JumpEdge(from=block 6, to=return block, instruction=return)>,
 <JumpEdge(from=block 7, to=return block, instruction=return)>)
```

#### Editing blocks

Say for example you wanted to change the value of `Test.field` from `0` to `17`, you could do this:

```python3
In [11]: graph[1].remove(kirjava.instructions.iconst_0)
    ...: graph[1].insert(1, kirjava.instructions.bipush(17))
Out[11]: <ConstantInstruction(opcode=0x10, mnemonic=bipush, constant=<Integer(17)>) at 7fc10a213480>
```

And just to check that we have edited the block correctly:

```python3
In [12]: graph[1]
Out[12]: <InsnBlock(label=1, instructions=[aload_0, bipush 17, putfield Test.field:I]) at 7fc10abc9f80>
```

#### Editing edges

Now let's edit an edge. Firstly let's find one that we can edit easily for the sake of tutorial:

```python3
In [13]: graph.out_edges(graph[2])
Out[13]: 
(<FallthroughEdge(from=block 2, to=block 3)>,
 <JumpEdge(from=block 2, to=block 4, instruction=ifgt)>)
```

Let's change the `ifgt` instruction into an `iflt` for this example:

```python3
In [14]: graph.jump(graph[2], graph[4], kirjava.instructions.iflt)
Out[14]: <JumpEdge(from=block 2, to=block 4, instruction=iflt)>
```

And, to check:

```python3
In [15]: graph.out_edges(graph[2])
Out[15]: 
(<FallthroughEdge(from=block 2, to=block 3)>,
 <JumpEdge(from=block 2, to=block 4, instruction=iflt)>)
```

As you can see we've managed to successfully edit the jump condition.  

There's a lot more that can be done than just these simple tutorials though **(have a play around!)**.

### Analysing bytecode

Often editing a method goes hand-in-hand with analysing it, and kirjava provides tools that allow you to statically analyse the data on the stack and in the locals via the use of the class `Trace`.

To create a trace for a method, you'll need to use the graph for said method. In this example, we'll use the graph from the previous examples:

```python3
In [16]: trace = kirjava.trace(graph)

In [17]: trace
Out[17]: <Trace(entries=9, exits=9, conflicts=0, subroutines=0, max_stack=2, max_locals=2) at 7fc10abff4c0>
```

And again, the more verbose method:

```python3
In [16]: trace = kirjava.analysis.Trace.from_graph(graph)

In [17]: trace
Out[17]: <Trace(entries=9, exits=9, conflicts=0, subroutines=0, max_stack=2, max_locals=2) at 7fc10abff4c0>
```

The `Trace` class provides pre/post liveness information (on a per-block basis) as well as information on subroutines, type conflicts and frames at block entries/exits.

For example, we could look at the local pre-liveness for block 3:

```python3
In [18]: trace.pre_liveness[graph[3]]
Out[18]: {1}
```

We could also view the state of the stack at the entry to it:

```python3
In [19]: trace.entries[graph[3]]
Out[19]: [<Frame(stack=[], locals={0=Test, 1=boolean}) at 7fc109ee7f10>]
```

And we can even inspect individual locals further:  

```python3
In [20]: trace.entries[graph[3]][0].locals
Out[20]: 
{0: <Entry(type=Test, constraints={Test, reference, java/lang/Object}) at 7fc109ee69d0>,
 1: <Entry(type=boolean, constraints={int, boolean}) at 7fc109ee7ce0>}

In [21]: trace.entries[graph[3]][0].locals[0].constraints
Out[21]: 
(<Entry.Constraint(type=reference, source=aload_0 @ block 1[0], original=False)>,
 <Entry.Constraint(type=Test, source=getfield Test.field:I @ block 2[1], original=False)>,
 <Entry.Constraint(type=Test, source=putfield Test.field:I @ block 1[2], original=False)>,
 <Entry.Constraint(type=java/lang/Object, source=None, original=True)>,
 <Entry.Constraint(type=Test, source=param 0 of Test#void test(boolean), original=True)>,
 <Entry.Constraint(type=reference, source=aload_0 @ block 2[0], original=False)>)

In [22]: trace.entries[graph[3]][0].locals[1].producers
Out[22]: 
(<InstructionInBlock(index=0, block=block 7, instruction=iinc 1 by 1)>,
 <Frame.Parameter(index=1, type=boolean, method=Test#void test(boolean))>)

In [23]: trace.entries[graph[3]][0].locals[1].consumers
Out[23]: 
(<InstructionInBlock(index=0, block=block 0, instruction=iload_1)>,
 <JumpEdge(from=block 0, to=block 2, instruction=ifne)>,
 <InstructionInBlock(index=0, block=block 5, instruction=iload_1)>,
 <JumpEdge(from=block 5, to=block 7, instruction=ifeq)>,
 <InstructionInBlock(index=0, block=block 7, instruction=iinc 1 by 1)>)
```

#### Assembly

Reassembling the method after editing is as easy as:

```python3
In [24]: kirjava.assemble(graph)
```

Or:

```python3
In [24]: graph.method.code = graph.assemble()
```

### Writing classfiles

Writing classfiles back out is also easy:

```python3
In [25]: kirjava.dump(cf, "Test-edited.class")
```

Or for the more verbose method:

```python3
In [25]: with open("Test-edited.class", "wb") as stream:
    ...:     cf.write(stream)
    ...: 
```

## "Trivia"

Yes, it is named after a character in HDM.  
The name is not a Java-related pun, but it does help that "java" is in the name.
