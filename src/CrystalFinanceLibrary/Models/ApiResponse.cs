using System.Text.Json.Serialization;

namespace CrystalFinanceLibrary.Models;

/// <summary>
/// Represents a standardized API response envelope with metadata and typed data.
/// </summary>
/// <typeparam name="T">The type of data contained in the response.</typeparam>
public class ApiResponse<T>
{
    /// <summary>
    /// Gets or sets a value indicating whether the API operation was successful.
    /// </summary>
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    /// <summary>
    /// Gets or sets the response message providing context about the operation result.
    /// </summary>
    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the actual data returned by the API operation.
    /// </summary>
    [JsonPropertyName("data")]
    public T Data { get; set; } = default!;
}
