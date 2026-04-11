using System.Text.Json.Serialization;

namespace CrystalFinance.Ui.Enums;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum TranSourceType
{
    Bank,
    Chase
}
