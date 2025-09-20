import ParallaxScrollView from "@/components/parallax-scroll-view";
import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { Collapsible } from "@/components/ui/collapsible";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Fonts } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
// Removed direct VariableType import to avoid runtime issues with polyfills
import React from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  TextInput,
} from "react-native";

import {
  addDatasetEntries,
  buildRule,
  ensureInitialized,
  getPrompt,
  getPrompts,
  getVariableType,
} from "@/services/maxim";

export default function MaximScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const inputTextStyle = [styles.input, { color: isDark ? '#fff' : '#000', borderColor: isDark ? '#444' : '#ccc', backgroundColor: isDark ? '#111' : '#fff' }];
  const multilineStyle = [styles.input, styles.multiline, { color: isDark ? '#fff' : '#000', borderColor: isDark ? '#444' : '#ccc', backgroundColor: isDark ? '#111' : '#fff' }];
  const placeholderColor = isDark ? '#888' : '#888';

  const [loadingAll, setLoadingAll] = React.useState(false);
  const [prompts, setPrompts] = React.useState<any[] | undefined>(undefined);

  const [loadingOne, setLoadingOne] = React.useState(false);
  const [promptId, setPromptId] = React.useState("");
  const [prompt, setPrompt] = React.useState<any | undefined>(undefined);

  const [datasetId, setDatasetId] = React.useState("");
  const [entriesJson, setEntriesJson] = React.useState(
    '[\n  {\n    "columnName": "Input",\n    "cellValue": { "type": "TEXT", "payload": "Doctor: Hi, what brings you in today?" }\n  },\n  {\n    "columnName": "Expected Output",\n    "cellValue": { "type": "TEXT", "payload": "Chief complaint: Sore throat and mild fever x1 day." }\n  }\n]'
  );
  const [addingDataset, setAddingDataset] = React.useState(false);
  const [VariableType, setVariableType] = React.useState<any>(null);

  React.useEffect(() => {
    ensureInitialized().catch(() => {});
    try {
      const VarType = getVariableType();
      setVariableType(VarType);
    } catch {
      // Ignore errors
    }
  }, []);

  const fetchAllPrompts = React.useCallback(async () => {
    try {
      setLoadingAll(true);
      const rule = await buildRule({
        deploymentVars: {
          tenant: "222",
          env: "prod",
        },
      });
      const res = await getPrompts(rule);
      setPrompts(res);
    } catch (e: any) {
      console.error('[MaximUI] getPrompts error', e);
      Alert.alert("Error", e?.message ?? String(e));
    } finally {
      setLoadingAll(false);
    }
  }, []);

  const fetchPromptById = React.useCallback(async () => {
    try {
      setLoadingOne(true);
      if (!promptId.trim()) {
        throw new Error("Enter a prompt id");
      }
      const rule = await buildRule({
        deploymentVars: {
          tenant: "111",
          env: "prod-2",
        },
      });
      const res = await getPrompt(promptId.trim(), rule);
      setPrompt(res);
    } catch (e: any) {
      console.error('[MaximUI] getPrompt error', e);
      Alert.alert("Error", e?.message ?? String(e));
    } finally {
      setLoadingOne(false);
    }
  }, [promptId]);

  function normalizeEntries(raw: any[]): any[] {
    return raw.map((entry) => {
      const e = { ...entry };
      const cv = e.cellValue ?? {};
      const t = cv.type;
      if (typeof t === 'string' && VariableType) {
        const key = t.startsWith('VariableType.') ? t.split('.').pop() : t;
        if (key && (VariableType as any)[key]) {
          cv.type = (VariableType as any)[key];
        }
      }
      e.cellValue = cv;
      return e;
    });
  }

  const onAddDatasetEntries = React.useCallback(async () => {
    try {
      setAddingDataset(true);
      if (!datasetId.trim()) throw new Error("Enter dataset id");
      let entries: any[];
      try {
        entries = JSON.parse(entriesJson);
        if (!Array.isArray(entries))
          throw new Error("Entries must be an array");
      } catch {
        throw new Error("Invalid entries JSON");
      }
      const normalized = normalizeEntries(entries);
      await addDatasetEntries(datasetId.trim(), normalized);
      console.log('[MaximUI] addDatasetEntries OK', { datasetId, count: normalized.length });
      Alert.alert("Dataset", "Entries added");
    } catch (e: any) {
      console.error('[MaximUI] addDatasetEntries error', e);
      Alert.alert("Error", e?.message ?? String(e));
    } finally {
      setAddingDataset(false);
    }
  }, [datasetId, entriesJson]);

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: "#D0D0D0", dark: "#353636" }}
      headerImage={
        <IconSymbol
          size={310}
          color="#808080"
          name="chevron.left.forwardslash.chevron.right"
          style={styles.headerImage}
        />
      }
    
    >
      <ThemedView style={styles.titleContainer}>
        <ThemedText
          type="title"
          style={{
            fontFamily: Fonts.rounded,
          }}
        >
          Maxim AI
        </ThemedText>
      </ThemedView>

      <Collapsible title="Prompt management">
        <ThemedView style={styles.section}>
          <ThemedText type="subtitle">Get all prompts</ThemedText>
          <ThemedText type="default">
            Deployment Vars - (env: 'prod', tenant: '222')
          </ThemedText>
          <Pressable
            onPress={fetchAllPrompts}
            disabled={loadingAll}
            style={styles.button}
          >
            {loadingAll ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <ThemedText style={styles.buttonText}>Fetch</ThemedText>
            )}
          </Pressable>
          {prompts && (
            <ThemedText style={styles.code}>
              {JSON.stringify(prompts, null, 2)}
            </ThemedText>
          )}
        </ThemedView>

        <ThemedView style={styles.section}>
          <ThemedText type="subtitle">Get prompt by ID</ThemedText>
          <ThemedText type="default">
            Deployment Vars - (promptId: 'cma6mbb92000n6zgirza9d7k7', env:
            'prod', tenant: '222')
          </ThemedText>
          <TextInput
            placeholder="prompt-id"
            value={promptId}
            onChangeText={setPromptId}
            autoCapitalize="none"
            autoCorrect={false}
            style={inputTextStyle}
            placeholderTextColor={placeholderColor}
          />
          <Pressable
            onPress={fetchPromptById}
            disabled={loadingOne}
            style={styles.button}
          >
            {loadingOne ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <ThemedText style={styles.buttonText}>Fetch</ThemedText>
            )}
          </Pressable>
          {prompt && (
            <ThemedText style={styles.code}>
              {JSON.stringify(prompt, null, 2)}
            </ThemedText>
          )}
        </ThemedView>
      </Collapsible>

      <Collapsible title="Dataset management">
        <ThemedView style={styles.section}>
          <ThemedText type="subtitle">Add entries</ThemedText>
          <ThemedText type="default">
            {'Shape: [{"columnName":"Input","cellValue":{"type":"TEXT","payload":"..."}}, ...]'}
          </ThemedText>
          <TextInput
            placeholder="dataset-id"
            value={datasetId}
            onChangeText={setDatasetId}
            autoCapitalize="none"
            autoCorrect={false}
            style={inputTextStyle}
            placeholderTextColor={placeholderColor}
          />
          <TextInput
            placeholder="entries (JSON array)"
            multiline
            value={entriesJson}
            onChangeText={setEntriesJson}
            autoCapitalize="none"
            autoCorrect={false}
            style={multilineStyle}
            placeholderTextColor={placeholderColor}
          />
          <Pressable onPress={onAddDatasetEntries} disabled={addingDataset} style={styles.button}>
            {addingDataset ? <ActivityIndicator color="#fff" /> : <ThemedText style={styles.buttonText}>Add</ThemedText>}
          </Pressable>
        </ThemedView>
      </Collapsible>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  headerImage: {
    color: "#808080",
    bottom: -90,
    left: -35,
    position: "absolute",
  },
  content: {
    padding: 16,
    gap: 16,
  },
  titleContainer: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 8,
  },
  section: {
    gap: 12,
    marginTop: 8,
    marginBottom: 24,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  multiline: {
    minHeight: 140,
    textAlignVertical: 'top',
  },
  button: {
    backgroundColor: "#3b82f6",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontWeight: "600",
  },
  code: {
    fontFamily: Fonts.mono,
    fontSize: 12,
  },
});
