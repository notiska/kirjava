public class SimpleExceptionTest {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Need at least one argument!");
            return;
        }
        String occurred = "false";
        String randomString = "hi!!!";
        try {
            int[] array = new int[Integer.decode(args[0])];
            if (array.length > 3) array[2] = 1;
        } catch (NegativeArraySizeException error) {
            occurred = "true";
        } catch (NumberFormatException error) {
            occurred = "true";
        }
        System.out.println(String.format("Exception occurred: %s", occurred));
        System.out.println(String.format("Random string: %s", randomString));
    }
}
