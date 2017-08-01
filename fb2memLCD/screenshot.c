// A simple demo using dispmanx to display get screenshot

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <assert.h>
#include <unistd.h>
#include <sys/time.h>

#include "bcm_host.h"

int main(void)
{
    DISPMANX_DISPLAY_HANDLE_T   display;
    DISPMANX_MODEINFO_T         info;
    DISPMANX_RESOURCE_HANDLE_T  resource;
    //VC_IMAGE_TYPE_T type = VC_IMAGE_RGB888;
	VC_IMAGE_TYPE_T type = VC_IMAGE_TF_1BPP;
    VC_IMAGE_TRANSFORM_T   transform = 0;
    VC_RECT_T         rect;

    void                       *image;
    uint32_t                    vc_image_ptr;

    int                   ret;

    uint32_t        screen = 0;

    bcm_host_init();

    printf("Open display[%i]...\n", screen );
    display = vc_dispmanx_display_open( screen );

    ret = vc_dispmanx_display_get_info(display, &info);
    assert(ret == 0);
    printf( "Display is %d x %d\n", info.width, info.height );

    image = calloc( 1, info.width * 3 * info.height );

    assert(image);

    resource = vc_dispmanx_resource_create( type,
                                                  info.width,
                                                  info.height,
                                                  &vc_image_ptr );

    vc_dispmanx_snapshot(display, resource, transform);

    vc_dispmanx_rect_set(&rect, 0, 0, info.width, info.height);
    vc_dispmanx_resource_read_data(resource, &rect, image, info.width*3); 

    FILE *fp = fopen("out.ppm", "wb");
    fprintf(fp, "P6\n%d %d\n255\n", info.width, info.height);
    fwrite(image, info.width*3*info.height, 1, fp);
    fclose(fp);

    ret = vc_dispmanx_resource_delete( resource );
    assert( ret == 0 );
    ret = vc_dispmanx_display_close(display );
    assert( ret == 0 );

    return 0;
}