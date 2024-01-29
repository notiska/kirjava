public class SimpleLoop {
    public static void main(String[] args) {
        int x = 100;
        if (args.length > 1) {
            while (x > 0) {
                --x;
            }
        } else {
            System.out.println(x);
        }
        System.out.println(x);
    }
}

