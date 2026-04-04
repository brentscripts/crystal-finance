using CrystalFinanceLibrary.Models;
using Microsoft.AspNetCore.Components.Forms;
using System.Net.Http.Json;

namespace CrystalFinance.Ui.Services
{
    public class TransactionProcessingService(HttpClient httpClient)
    {
        private readonly HttpClient _httpClient = httpClient;
        
        public async Task<List<TransactionModel>> ImportFileAsync(IBrowserFile file, string source)
        {
            using var content = new MultipartFormDataContent();

            var fileContent = new StreamContent(file.OpenReadStream(maxAllowedSize: 10 * 1024 * 1024)); // Limit to 10 MB
            content.Add(fileContent, "file", file.Name);

            var response = await _httpClient.PostAsync($"api/transactions/import?source={Uri.EscapeDataString(source)}", content);
            response.EnsureSuccessStatusCode();

            return await response.Content.ReadFromJsonAsync<List<TransactionModel>>() ?? new();
        }
    }
}
