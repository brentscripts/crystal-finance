using CrystalFinance.Api.Startup;

var builder = WebApplication.CreateBuilder(args);

builder.AddDependencies();
builder.AddAuthentication();

var app = builder.Build();

app.UseOpenApi();

app.UseHttpsRedirection();

app.UseAuthentication();

app.UseAuthorization();

app.MapControllers();

app.Run();
