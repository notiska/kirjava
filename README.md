# Kirjava
A Java bytecode manipulation library for Python.  
Still very much a WIP, but hopefully it'll be somewhat usable eventually.  

**Disclaimer:** It is probably quite buggy as it stands, but I am working on version 0.1.2 (slowly), which contains a lot of improvements.

## Why?
I use this library in quite a few of my projects now so it's nicer to have it in one place at this point.  
In its current state, I don't expect it to be used by anyone else, but if you do find some use in it, awesome :).  
The API is unfortunately quite limited (see limitations) and somewhat unintuitive right now, I have plans to improve it in the future.  

## Limitations
1. Missing quite a few attributes.
2. No jar file reading yet, even though the package exists.
3. Although there is generic signature parsing, writing generic signatures is not yet implemented.
4. No direct access to method trace information (WIP).
5. No graph transformations are implemented yet (WIP).
6. No support for `jsr/ret` instructions (WIP).
7. Stack underflows crash the assembler, even with `no_verify=True`.
8. No support for invalid CP entries when it comes to UTF8 constants, as most of them are dereferenced. (I can't think of a nice solution to this problem without perhaps using descriptors, and even then.)

## Quickstart
I might add documentation in the future, not sure yet lol. Anyway, some basic examples:

### Getting started
```python3
In [1]: import kirjava
   ...: environ = kirjava.initialise(
   ...:     load_skeletons=True,  # Load "skeleton classes" (info about classes in rt.jar).
   ...:     version=kirjava.version.Version.get("11"),  # Use skeleton classes from Java 11.
   ...: )
```
Kirjava bases all information (currently just classes) around an `kirjava.environment.Environment` instance, so we need to initialise this
instance to use Kirjava.  

### Reading classfiles
```python3
In [2]: with open("Test.class", "rb") as stream:
   ...:     cf = kirjava.ClassFile.read(stream)
   ...: 

In [3]: cf
Out[3]: <ClassFile(name='Test') at 7fc81707e940>
```

We can view all the methods in the classfile:
```python3
In [4]: cf.methods
Out[4]: 
(<MethodInfo(name='main', argument_types=(java/lang/String[],), return_type=void) at 7fc8179ba1a0>,
 <MethodInfo(name='<init>', argument_types=(), return_type=void) at 7fc814bd02e0>,
 <MethodInfo(name='test', argument_types=(boolean,), return_type=void) at 7fc814bd0dc0>,
 <MethodInfo(name='test2', argument_types=(), return_type=void) at 7fc814bd3700>)
```

We can also view all the fields in the classfile:
```python3
In [5]: cf.fields
Out[5]: (<FieldInfo(name='field', type=int) at 7fc8170aab60>,)
```

### Editing methods
This is a more major feature (which still requires a lot of work unfortunately).  
To abstract away some of the annoyances of creating valid bytecode, we can use `kirava.analysis.Graph`:
```python3
In [6]: graph = kirjava.analysis.Graph.disassemble(cf.get_method("test"))
   ...: graph.blocks  # The basic blocks that the disassembler created
Out[6]: 
[<Block(label=0) at 7fc815b37ac0>,
 <Block(label=1) at 7fc817a1ccd0>,
 <Block(label=2) at 7fc817a1e950>,
 <Block(label=3) at 7fc8170ed030>,
 <Block(label=4) at 7fc8170efa30>,
 <Block(label=5) at 7fc8170ef0a0>,
 <Block(label=6) at 7fc8156248b0>,
 <Block(label=7) at 7fc815624400>]
```

... transformations to the graph can be done here.

To reassemble the method:
```python3
In [7]: code = graph.assemble(
   ...:     cf,  # Need to specify the classfile
   ...:     no_verify=False,
   ...:     compute_frames=True,  # Computes stackmap frames if necessary
   ...:     sort_blocks=True,  # Write the blocks in order of their labels, otherwise the order is arbitrary
   ...: )
   ...: code
Out[7]: <Code(max_stack=3, max_locals=2, exception_table=[]) at 7fc814a72ea0>
In [8]: cf.get_method("test").attributes[code.name] = (code,)  # Put this code attribute back into the method
```
Note here that we have to use a tuple with attributes, this is because it is possible for a classfile to have multiple attributes
with the same name, unfortunately.

### Writing classfiles
```python3
In [9]: with open("Test.class", "wb") as stream:
   ...:     cf.write(stream)
   ...: 
```
