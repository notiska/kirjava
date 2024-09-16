/**
 * Adapted from: https://github.com/GenericException/SkidSuite/blob/master/obf-techniques/invokedynamic.md
 */
public class IndyTest1 {
    public static void main(String[] args) {
        exec(IndyTest1::hi);
    }

    static void hi() {
        System.out.println("hi");
    }

    static void exec(Runnable runnable) {
        runnable.run();
    }
}
