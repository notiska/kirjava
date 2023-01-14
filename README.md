# Kirjava
A Java bytecode manipulation library for Python.  

**Disclaimer:** This library is still very much a WIP and is probably quite buggy, I am working to fix as many as I come across.

## Why?
I use this library in quite a few of my projects now so it's nicer to have it in one place at this point.  
In its current state, I don't expect it to be used by anyone else, but if you do find some use in it, awesome :).  
The API is unfortunately quite limited (see limitations) and somewhat unintuitive right now, I have plans to improve it in the future.  

## Limitations
1. Missing quite a few attributes.
2. No jar file reading yet, even though the package exists.
3. Although there is generic signature parsing, writing generic signatures is not yet implemented.
4. Doesn't appear to handle multi-source uninitialized types correctly in the StackMapTable?
5. The performance is good, but could still be improved.

## Quickstart
I might add documentation in the future, not sure yet lol. Anyway, here's the quickstart guide, for more usage, see [examples](examples/).

### Installing
You can either:
1. Clone this repository and install via `python3 setup.py install`.
2. Install this library via pip: `pip3 install git+https://github.com/node3112/kirjava.git`.

### Getting started
```python3
In [1]: import kirjava
   ...: kirjava.initialise(
   ...:     load_skeletons=True,  # Load "skeleton classes" (info about classes in rt.jar).
   ...:     skeletons_version=kirjava.version.Version.get("11"),  # Use skeleton classes from Java 11.
   ...: )
```
Kirjava bases all information (currently just classes) around the `kirjava.environment.Environment` class. Calling `kirjava.initialise` simply loads the skelton
classes as of right now, it may do more in the future however.  
**Note:** it is not always necessary to perform this step, if the assembler (or Java) gives errors though, you may want to.

### Reading classfiles
```python3
In [2]: with open("Test.class", "rb") as stream:
   ...:     cf = kirjava.ClassFile.read(stream)
   ...: 

In [3]: cf
Out[3]: <ClassFile(name='Test') at 7ffab11a5740>
```

We can view all the methods in the classfile:
```python3
In [4]: cf.methods
Out[4]: 
(<MethodInfo(name='main', argument_types=(java/lang/String[],), return_type=void) at 7ffab12251e0>,
 <MethodInfo(name='<init>', argument_types=(), return_type=void) at 7ffab11e0d60>,
 <MethodInfo(name='test', argument_types=(boolean,), return_type=void) at 7ffab11e0880>,
 <MethodInfo(name='test2', argument_types=(), return_type=void) at 7ffab11e0b80>)
```

We can also view all the fields in the classfile:
```python3
In [5]: cf.fields
Out[5]: (<FieldInfo(name='field', type=int) at 7ffab12254e0>,)
```

### Editing methods  
To abstract away some of the annoyances of creating valid bytecode, we can use `kirava.analysis.InsnGraph`:
```python3
In [6]: graph = kirjava.analysis.InsnGraph.disassemble(cf.get_method("test"))
   ...: graph.blocks  # The basic blocks that the disassembler created
Out[6]: 
(<InsnBlock(label=0, instructions=[iload_1, ifne]) at 7ffab128b6a0>,
 <InsnBlock(label=1, instructions=[aload_0, iconst_0, putfield Test#int field]) at 7ffab1138770>,
 <InsnBlock(label=2, instructions=[aload_0, getfield Test#int field, ifgt]) at 7ffab14d6ac0>,
 <InsnBlock(label=3, instructions=[iconst_0, ifeq]) at 7ffab128a7f0>,
 <InsnBlock(label=5, instructions=[iload_1, ifeq]) at 7ffab14d67a0>,
 <InsnBlock(label=7, instructions=[iinc 1 by 1]) at 7ffab14d66b0>)
```

... transformations to the graph and blocks can be done here.

To reassemble the method:
```python3
In [7]: code = graph.assemble()
   ...: code
Out[7]: <Code(max_stack=3, max_locals=2, exception_table=[]) at 7ffab1210900>
In [8]: cf.get_method("test").code = code  # Put this code attribute back into the method
```

### Writing classfiles
```python3
In [9]: with open("Test.class", "wb") as stream:
   ...:     cf.write(stream)
   ...: 
```
