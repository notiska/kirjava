/**
 * Read the notice from SuperTest1.
 */
public class SuperTest2 extends SuperTest1 {

    public String index = "hello";

    public SuperTest2(int index) {
        super(index);

        System.out.println(index);
        System.out.println(this.index);
        System.out.println(super.index);
        
        System.out.println(test());
        System.out.println(super.test());
    }
    
    @Override
    public String test2() {
        return "SuperTest2";
    }
}
