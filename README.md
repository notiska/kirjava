# Kirjava
A Java bytecode library for Python.  

**Active development is mostly done on the `dev` branch, if you're curious about new features.**

## Quickstart
I might add documentation in the future, not sure yet lol. Anyway, here's the quickstart guide, for more usage, see [examples](examples/).

### Installing
You can either:
1. Clone this repository and install via `python3 setup.py install`.
2. Install this library via pip: `pip3 install git+https://github.com/node3112/kirjava.git`.

**You will need `python>=3.8` for this library to work correctly, any other versions are untested.**

### Getting started
```python3
In [1]: import kirjava
   ...: kirjava.initialise(
   ...:     load_skeletons=True,  # Load "skeleton classes" (info about classes in rt.jar).
   ...:     skeletons_version=kirjava.version.Version.get("11"),  # Use skeleton classes from Java 11.
   ...: )
```
Kirjava bases all information (currently just classes) around the `kirjava.environment` module. Calling `kirjava.initialise` simply loads the skelton
classes as of right now, it may do more in the future however.  
**Note:** it is not always necessary to perform this step, if the assembler (or Java) gives errors though, you may want to.

### Reading classfiles
```python3
In [2]: cf = kirjava.load("Test.class")
   ...: # This code is a shortcut, and is roughly equivalent to:
   ...: # with open("Test.class", "rb") as stream:
   ...: #     cf = kirjava.ClassFile.read(stream)

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
In [6]: graph = kirjava.disassemble(cf.get_method("test"))
   ...: # This is another shortcut, roughly equivalent to:
   ...: # graph = kirjava.analysis.InsnGraph.disassemble(cf.get_method("test").code)

In [7]: graph.blocks  # The basic blocks that the disassembler created
Out[7]: 
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
In [8]: kirjava.assemble(graph)
   ...: # This shortcut is roughly equivalent to:
   ...: # graph.method.code = graph.assemble()
```

### Writing classfiles
```python3
In [9]: kirjava.dump(cf, "Test.class")
   ...: # This shortcut is roughly equivalent to:
   ...: # with open("Test.class", "wb") as stream:
   ...: #     cf.write(stream)
```

## Limitations
(Stuff I still need to do, there are also a lot of todos scattered throughout the source).

1. Missing some less important attributes.
2. No jar file reading yet, even though the package exists.
3. Although there is generic signature parsing, writing generic signatures is not yet implemented.
4. The assembler is slow and cannot handle certain edge cases.
