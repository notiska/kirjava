public class Test {
    public static void main(String args[]) {
        // This is horrible, I hate early Java.
        Class sdiofx = /* float.class */ new Float(5.0f).getClass();
        Object test = null;
        double testDouble = 9.0;

        Object[] objectArray = new Object[1];
        if (args.length > 1) {
            objectArray = new String[1];
        } else {
            objectArray = new Integer[1];
        }

        double[] testArray = new double[1];
        testArray[0] = 1.0;
        System.out.println(testArray[0] + 2.0);

        Object x = new Test((Object)testArray); // Silly type cast needed here.

        switch (args.length) {
            case 0: {
                test = "zero";
                break;
            }
            case 1: {
                test = "one";
                break;
            }
            case 2: {
                test = "two";
                break;
            }
            case 3: {
                test = "three";
                break;
            }
            default: {
                test = "many";
                break;
            }
        }

        System.out.println(test);
        System.out.println(testDouble);
        System.out.println(x);
        System.out.println((Object)objectArray); // Silly cast needed here.
        System.out.println("Hello, world!");
    }

    private int x;

    public Test(Object param) {
        x += 5;
    }
}
