#include "raylib.h"
#include <stdint.h>

#define GAME_WIDTH 240
#define GAME_HEIGHT 208
#define WINDOW_WIDTH 1366
#define WINDOW_HEIGHT 768

RenderTexture2D target;

void draw_game() 
{
    float windowWidth = (float)GetScreenWidth();
    float windowHeight = (float)GetScreenHeight();

    float horizontalScale = windowWidth / GAME_WIDTH;
    float verticalScale = windowHeight / GAME_HEIGHT;

    float scale = (horizontalScale < verticalScale)
        ? horizontalScale
        : verticalScale;

    float desiredWidth = GAME_WIDTH * scale;
    float desiredHeight = GAME_HEIGHT * scale;

    float desiredX = (windowWidth - desiredWidth) * 0.5f;
    float desiredY = (windowHeight - desiredHeight) * 0.5f;

    DrawTexturePro(
        target.texture,
        (Rectangle){ 0, 0, GAME_WIDTH, -GAME_HEIGHT },
        (Rectangle){ desiredX, desiredY, desiredWidth, desiredHeight },
        (Vector2){ 0, 0 },
        0,
        WHITE
    );
}

#define TILEMAP_WIDTH 15
#define TILEMAP_HEIGHT 13
#define TILE_SIZE 16

void draw_tilemap()
{
    uint32_t x = 0, y = 0;
    for (int i = 0; i < TILEMAP_WIDTH; i++) {
         x = i * TILE_SIZE;
         for( int j = 0; j < TILEMAP_HEIGHT; j++) 
         {
             y = j * TILE_SIZE;
             DrawRectangleLines(x, y, TILE_SIZE, TILE_SIZE, RED);
         }
    }
}

int main()
{
    SetConfigFlags(FLAG_WINDOW_RESIZABLE);
    InitWindow(WINDOW_WIDTH, WINDOW_HEIGHT, "BomberC");
    target = LoadRenderTexture(GAME_WIDTH, GAME_HEIGHT);

    while (!WindowShouldClose()) {
        BeginTextureMode(target);
            ClearBackground(MAGENTA);
            draw_tilemap();
        EndTextureMode();

        BeginDrawing();
            DrawFPS(10, 10);
            ClearBackground(RED);
            draw_game();
        EndDrawing();
    }

    UnloadRenderTexture(target);
    CloseWindow();

    return 0;
}
