#include "raylib.h"

#include "grid.h"
#include "input.h"
#include "maps.h"
#include "scene.h"
#include <stdio.h>

#define WINDOW_WIDTH 1366
#define WINDOW_HEIGHT 768
#define ASPECT_WIDTH 16.0f
#define ASPECT_HEIGHT 9.0f

#define TICK_PERIOD_SECONDS (1.0 / SCENE_TICKS_PER_SECOND)
// On a machine too slow to keep up, the game runs in slow motion instead of falling further behind every frame.
#define MAX_TICKS_PER_FRAME 5

static const Color PANEL_COLOR = { 36, 28, 52, 255 };

static Rectangle fit_rect(float contentWidth, float contentHeight, Rectangle bounds)
{
    float horizontalScale = bounds.width / contentWidth;
    float verticalScale = bounds.height / contentHeight;

    float scale = (horizontalScale < verticalScale)
        ? horizontalScale
        : verticalScale;

    float desiredWidth = contentWidth * scale;
    float desiredHeight = contentHeight * scale;

    float desiredX = bounds.x + (bounds.width - desiredWidth) * 0.5f;
    float desiredY = bounds.y + (bounds.height - desiredHeight) * 0.5f;

    return (Rectangle){ desiredX, desiredY, desiredWidth, desiredHeight };
}

static void draw_game(RenderTexture2D arena)
{
    Rectangle window = { 0, 0, (float)GetScreenWidth(), (float)GetScreenHeight() };
    Rectangle screen = fit_rect(ASPECT_WIDTH, ASPECT_HEIGHT, window);
    DrawRectangleRec(screen, PANEL_COLOR);

    float arenaWidth = (float)arena.texture.width;
    float arenaHeight = (float)arena.texture.height;
    DrawTexturePro(
        arena.texture,
        // Negative height: render textures are stored upside down (OpenGL).
        (Rectangle){ 0, 0, arenaWidth, -arenaHeight },
        fit_rect(arenaWidth, arenaHeight, screen),
        (Vector2){ 0, 0 },
        0,
        WHITE
    );
}


int main(void)
{
    Scene scene = scene_create_arena(MAP_PLAYGROUND.text);
    if (scene.tilemap.width == 0) {
        return 1;
    }

    SetConfigFlags(FLAG_WINDOW_RESIZABLE);
    InitWindow(WINDOW_WIDTH, WINDOW_HEIGHT, "BomberC");

    RenderTexture2D arena = LoadRenderTexture(
        grid_cell_to_px(scene.tilemap.width),
        grid_cell_to_px(scene.tilemap.height)
    );

    Input input = { 0 };
    double previous_time = GetTime();
    double accumulator = 0.0;

    while (!WindowShouldClose()) {

        double now = GetTime();
        accumulator += now - previous_time;
        previous_time = now;
        if (accumulator > MAX_TICKS_PER_FRAME * TICK_PERIOD_SECONDS)
            accumulator = MAX_TICKS_PER_FRAME * TICK_PERIOD_SECONDS;

        input_poll(&input);
        while (accumulator >= TICK_PERIOD_SECONDS) {
            scene_tick(&scene, input_take(&input));
            accumulator -= TICK_PERIOD_SECONDS;
        }

        BeginTextureMode(arena);
            ClearBackground(MAGENTA);
            scene_draw(&scene);
        EndTextureMode();

        BeginDrawing();
            ClearBackground(BLACK);
            draw_game(arena);
            DrawFPS(10, 10);
        EndDrawing();
    }

    UnloadRenderTexture(arena);
    CloseWindow();

    return 0;
}
