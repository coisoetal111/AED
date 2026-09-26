#include<stdio.h>
#include<stdlib.h>


unsigned long long power(int k);
int main(int argc, int *argv){

    int N,p;
    unsigned long long h,result = 0;
    printf("N e p:");
    scanf("%d %d",&N,&p);
    
    for(int i = 0; i <= N; i++){
        h = 1;
        for (int j = 1; j <= i; j++) h *= i;
        //printf("%lld ", h);
        result += h;
       


    }
    result %= p;

    printf("\n%lld\n", result);

    return 0;


}

unsigned long long power(int k){
    unsigned long long result = k;
    for (int i = 0; i < k; i++)
    {
        result *= k;
    }
    
 return result;

}