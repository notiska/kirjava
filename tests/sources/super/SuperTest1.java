/**
 * These were mainly made to test my decompiler (which is now private) but may server some use in kirjava?
 * I'll leave them here anyway.
 */
public class SuperTest1 {

    protected int index = 0;

    public SuperTest1(int index) {
        this.index = index;
    }
    
    public String test() {
        return "hello!";
    }

    public String test2() {
        return "SuperTest1";
    }
}
