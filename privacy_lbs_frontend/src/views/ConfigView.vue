<template>
  <div class="config-view">
    <!-- Top bar -->
    <div class="config-topbar">
      <div class="topbar-left">
        <span class="topbar-title">System Configuration</span>
        <span class="topbar-subtitle">SKTAQ · Paillier Homomorphic Encryption Parameter Management</span>
      </div>
      <div class="topbar-actions">
        <el-button @click="handleRestore" plain size="small">Restore Default</el-button>
        <el-button type="primary" @click="handleSave" :icon="Check" size="small">Save Configuration</el-button>
      </div>
    </div>

    <!-- Main three columns -->
    <div class="config-body">
      <!-- ── Left column: Navigation ── -->
      <aside class="config-nav">
        <div
          v-for="item in navItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeSection === item.key }"
          @click="activeSection = item.key"
        >
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-label">{{ item.label }}</span>
        </div>
      </aside>

      <!-- ── Middle column: Config form ── -->
      <main class="config-main">
        <!-- Module 1: Encryption config -->
        <section v-show="activeSection === 'crypto'" class="config-section">
          <div class="section-header">
            <h2 class="section-title">Encryption Configuration</h2>
            <span class="section-badge">Paillier Homomorphic Encryption</span>
          </div>

          <div class="form-grid">
            <!-- Left side form -->
            <el-form label-position="top" class="config-form">
              <el-form-item label="Key Length">
                <el-radio-group v-model="cfg.keySize" class="key-size-group">
                  <el-radio-button :value="512">512 bit</el-radio-button>
                  <el-radio-button :value="1024">1024 bit</el-radio-button>
                  <el-radio-button :value="2048">2048 bit</el-radio-button>
                </el-radio-group>
                <div class="field-hint">Longer keys provide higher security but increase encryption time</div>
              </el-form-item>

              <el-form-item label="Encryption Time Estimate (100 records)">
                <div class="estimate-bar">
                  <el-progress
                    :percentage="Math.min(100, Math.round(cfg.estimateEncryptionMs() / 20))"
                    :stroke-width="12"
                    :color="estimateColor"
                    :show-text="false"
                    style="flex:1"
                  />
                  <span class="estimate-label">≈ {{ cfg.estimateEncryptionMs() }} ms</span>
                </div>
              </el-form-item>

              <el-form-item label="Key Status">
                <div class="key-status">
                  <el-tag :type="cfg.keysGenerated ? 'success' : 'info'" size="large">
                    {{ cfg.keysGenerated ? 'Keys Generated' : 'Keys Not Generated' }}
                  </el-tag>
                  <span v-if="cfg.keyGenTimeMs > 0" class="key-time">Time: {{ cfg.keyGenTimeMs }} ms</span>
                  <el-tag v-if="cfg.keyDigest" type="warning" effect="plain" size="small">
                    Fingerprint: {{ digestDisplay }}
                  </el-tag>
                </div>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" :loading="generatingKey" @click="handleGenerateKey" style="width:100%">
                  {{ generatingKey ? 'Generating...' : 'Generate Key Pair' }}
                </el-button>
              </el-form-item>

              <template v-if="cfg.privateKeyRaw">
                <el-form-item>
                  <el-button type="warning" :icon="Download" style="width:100%" @click="handleDownloadPrivateKey">
                    Download Private Key (private_key.json)
                  </el-button>
                </el-form-item>
                <el-alert type="warning" :closable="false" show-icon style="margin-top:-12px">
                  <template #default>
                    <span style="font-size:12px;line-height:1.6">
                      Please save your private key securely. Based on homomorphic encryption security protocol, <strong>this system does not store the private key in the cloud</strong>. The private key will be cleared from memory after page refresh.
                    </span>
                  </template>
                </el-alert>

                <!-- ── Key deployment architecture hint ── -->
                <el-form-item style="margin-top:12px">
                  <div class="key-flow-panel">
                    <div class="kf-header-row">
                      <div class="kf-title">
                        <span class="kf-title-icon">⚡</span>
                        Key Distribution Flow
                      </div>
                      <!-- Deploy button -->
                      <button
                        class="deploy-btn"
                        :class="{
                          'deploy-btn-ready':    deployStatus === 'idle',
                          'deploy-btn-loading':  deployStatus === 'deploying',
                          'deploy-btn-done':     deployStatus === 'done',
                        }"
                        :disabled="deployStatus !== 'idle'"
                        @click="handleDeployKeys"
                      >
                        <span v-if="deployStatus === 'idle'" class="deploy-btn-inner">
                          <span class="deploy-icon">🚀</span> Deploy Cluster Keys
                        </span>
                        <span v-else-if="deployStatus === 'deploying'" class="deploy-btn-inner">
                          <span class="deploy-spinner"></span> Establishing secure channel...
                        </span>
                        <span v-else class="deploy-btn-inner">
                          <span class="deploy-icon">✅</span> Deployed Successfully
                        </span>
                      </button>
                    </div>

                    <div class="kf-items">
                      <!-- PK flow -->
                      <div class="kf-item kf-item-pk" :class="{ 'kf-item-active': pkDeployed }">
                        <div class="kf-left">
                          <span class="kf-key-badge kf-pk">PK</span>
                          <span class="kf-key-label">Public Key</span>
                        </div>
                        <div class="kf-arrow" :class="{ 'kf-arrow-flowing': deployFlowing || pkDeployed }">
                          <svg width="28" height="12" viewBox="0 0 28 12">
                            <line x1="0" y1="6" x2="22" y2="6" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="3 2"/>
                            <polygon points="22,2 28,6 22,10" fill="#38bdf8"/>
                          </svg>
                        </div>
                        <div class="kf-right">
                          <span class="kf-dest">Main Cloud C1 &amp; All Fog Nodes</span>
                          <span class="kf-desc">Used for client-side encryption and cloud-fog node verification</span>
                        </div>
                        <div class="kf-status-tag" :class="pkDeployed ? 'kf-tag-synced' : 'kf-tag-pending'">
                          {{ pkDeployed ? '✓ Synced' : 'Pending' }}
                        </div>
                      </div>
                      <!-- SK flow -->
                      <div class="kf-item kf-item-sk" :class="{ 'kf-item-active-sk': skDeployed }">
                        <div class="kf-left">
                          <span class="kf-key-badge kf-sk">SK</span>
                          <span class="kf-key-label">Private Key</span>
                        </div>
                        <div class="kf-arrow" :class="{ 'kf-arrow-flowing-sk': deployFlowing || skDeployed }">
                          <svg width="28" height="12" viewBox="0 0 28 12">
                            <line x1="0" y1="6" x2="22" y2="6" stroke="#34d399" stroke-width="1.5" stroke-dasharray="3 2"/>
                            <polygon points="22,2 28,6 22,10" fill="#34d399"/>
                          </svg>
                        </div>
                        <div class="kf-right">
                          <div class="kf-dest-row">
                            <span class="kf-dest kf-dest-secure">Trusted Cloud C2 (Physically Isolated)</span>
                            <span class="kf-shield">🛡️</span>
                          </div>
                          <span class="kf-desc">Physically isolated custody, only used for backend secure decryption, DO does not distribute to any user</span>
                        </div>
                        <div class="kf-status-tag" :class="skDeployed ? 'kf-tag-locked' : 'kf-tag-pending'">
                          {{ skDeployed ? 'Locked' : 'Pending Distribution' }}
                        </div>
                      </div>
                    </div>
                    <div class="kf-footer">
                      End users (Client) only receive PK · Private key (SK) never leaves the trusted environment
                    </div>
                  </div>
                </el-form-item>
              </template>
            </el-form>

            <!-- Right side key visualization -->
            <div class="crypto-visual">
              <div class="cv-title">Security Strength Visualization</div>
              <div class="cv-ring-wrap">
                <svg viewBox="0 0 160 160" class="cv-ring">
                  <circle cx="80" cy="80" r="64" fill="none" stroke="#1e293b" stroke-width="12"/>
                  <circle cx="80" cy="80" r="64" fill="none"
                    :stroke="estimateColor"
                    stroke-width="12"
                    stroke-linecap="round"
                    :stroke-dasharray="`${keySizePercent * 4.02} 999`"
                    transform="rotate(-90 80 80)"
                    style="transition: stroke-dasharray 0.6s ease"
                  />
                  <text x="80" y="74" text-anchor="middle" font-size="22" font-weight="700" :fill="estimateColor">{{ cfg.keySize }}</text>
                  <text x="80" y="94" text-anchor="middle" font-size="11" fill="#64748b">bit</text>
                </svg>
              </div>
              <div class="cv-levels">
                <div class="cv-level" :class="{ active: cfg.keySize >= 512 }">
                  <span class="cv-dot" style="background:#f59e0b"></span>Basic Security 512bit
                </div>
                <div class="cv-level" :class="{ active: cfg.keySize >= 1024 }">
                  <span class="cv-dot" style="background:#38bdf8"></span>Standard Security 1024bit
                </div>
                <div class="cv-level" :class="{ active: cfg.keySize >= 2048 }">
                  <span class="cv-dot" style="background:#34d399"></span>High Strength Security 2048bit
                </div>
              </div>
            </div>
          </div>

          <!-- ── Fog node topology config ── -->
          <div class="fog-module">
            <div class="fog-module-header">
              <span class="fog-module-title">Fog Node Topology Configuration</span>
              <span class="fog-module-badge">Quadtree Grid Partition</span>
              <span class="fog-online-badge"><span class="fog-online-dot"></span>{{ fogNodeCount }} NODES ONLINE</span>
            </div>

            <!-- Slider area -->
            <div class="fog-slider-section">
              <div class="fog-level-labels">
                <span :class="{ 'fog-lv-active': demoApp.fogLevel === 1 }">Lv.1 · 4 cells</span>
                <span :class="{ 'fog-lv-active': demoApp.fogLevel === 2 }">Lv.2 · 16 cells</span>
                <span :class="{ 'fog-lv-active': demoApp.fogLevel === 3 }">Lv.3 · 64 cells</span>
              </div>
              <el-slider
                :model-value="demoApp.fogLevel"
                @update:model-value="(v: number) => demoApp.setFogLevel(v)"
                :min="1" :max="3" :step="1" :show-stops="true"
                :marks="{ 1: 'Lv.1', 2: 'Lv.2', 3: 'Lv.3' }"
                class="fog-slider"
              />
              <div class="fog-slider-hint">
                Note: After setting the cluster size, the system will dynamically divide the quadtree grid and distribute based on this number (num(FS)) during data import.
              </div>
            </div>

            <!-- Cloud node cards -->
            <div class="cloud-nodes-row">
              <!-- C1 main cloud -->
              <el-tooltip placement="bottom" effect="dark" :show-after="200">
                <template #content>
                  <div class="cn-tooltip">
                    <div class="cnt-title">Cloud Server C1</div>
                    <div class="cnt-row"><span class="cnt-key">CPU</span><span class="cnt-val">{{ c1Active ? '12%' : '--' }}</span></div>
                    <div class="cnt-row"><span class="cnt-key">RAM</span><span class="cnt-val">{{ c1Active ? '3.8 GB / 16 GB' : '--' }}</span></div>
                    <div class="cnt-row"><span class="cnt-key">IP</span><span class="cnt-val">10.0.0.1:8443</span></div>
                    <div class="cnt-row"><span class="cnt-key">Status</span><span class="cnt-val" :style="{color: c1Active ? '#34d399' : '#94a3b8'}">{{ c1Active ? 'Listening for encrypted requests' : 'Standby' }}</span></div>
                    <div class="cnt-row"><span class="cnt-key">SGL Index</span><span class="cnt-val">{{ c1Active ? 'Loaded · 48,920 records' : 'Not loaded' }}</span></div>
                  </div>
                </template>
                <div class="cloud-node-card cloud-node-c1" :class="{ 'cn-active': c1Active, 'cn-standby': !c1Active }">
                  <div class="cn-header">
                    <span class="cn-online-dot" :class="c1Active ? 'cn-dot-online' : 'cn-dot-standby'"></span>
                    <span class="cn-online-label" :style="{color: c1Active ? '#38bdf8' : '#475569'}">{{ c1Active ? 'ONLINE' : 'STANDBY' }}</span>
                    <span class="cn-type-badge">Cloud Server</span>
                  </div>
                  <div class="cn-name">Main Cloud C1</div>
                  <div class="cn-subtitle">Cloud Server 1</div>
                  <div class="cn-duties">
                    <div class="cn-duty"><span class="cn-duty-dot" style="background:#38bdf8"></span>Ready to receive full Secure Global Index (SGL)</div>
                  <div class="cn-duty-status-hint">Waiting for data flow input...</div>
                    <div class="cn-duty"><span class="cn-duty-dot" style="background:#38bdf8"></span>Execute ciphertext spatial pruning</div>
                    <div class="cn-duty"><span class="cn-duty-dot" style="background:#38bdf8"></span>Route query to fog nodes</div>
                  </div>
                  <div class="cn-key-tag cn-pk-tag">Holds PK</div>
                </div>
              </el-tooltip>

              <!-- Connection arrows -->
              <div class="cloud-connector">
                <svg width="60" height="40" viewBox="0 0 60 40">
                  <line x1="0" y1="20" x2="52" y2="20" stroke="#475569" stroke-width="1" stroke-dasharray="4 3"/>
                  <polygon points="52,16 60,20 52,24" fill="#475569"/>
                </svg>
                <span class="cloud-connector-label">Secure Protocol</span>
              </div>

              <!-- C2 trusted cloud -->
              <el-tooltip placement="bottom" effect="dark" :show-after="200">
                <template #content>
                  <div class="cn-tooltip">
                    <div class="cnt-title">Trusted Cloud C2 (TEE Enclave)</div>
                    <div class="cnt-row"><span class="cnt-key">CPU</span><span class="cnt-val">{{ c2Active ? '8%' : '--' }}</span></div>
                    <div class="cnt-row"><span class="cnt-key">RAM</span><span class="cnt-val">{{ c2Active ? '2.1 GB / 8 GB' : '--' }}</span></div>
                    <div class="cnt-row"><span class="cnt-key">IP</span><span class="cnt-val">10.0.0.2:9443</span></div>
                    <div class="cnt-row"><span class="cnt-key">Status</span><span class="cnt-val" :style="{color: c2Active ? '#34d399' : '#94a3b8'}">{{ c2Active ? 'Private Key Enclave Locked' : 'Standby' }}</span></div>
                    <div class="cnt-row"><span class="cnt-key">SK Status</span><span class="cnt-val" style="color:#34d399">{{ c2Active ? '🔒 Physical isolation, memory encryption' : 'Not loaded' }}</span></div>
                  </div>
                </template>
                <div class="cloud-node-card cloud-node-c2" :class="{ 'cn-active-c2': c2Active, 'cn-standby': !c2Active }">
                  <div class="cn-header">
                    <span class="cn-online-dot" :class="c2Active ? 'cn-dot-online-c2' : 'cn-dot-standby'"></span>
                    <span class="cn-online-label" :style="{color: c2Active ? '#34d399' : '#475569'}">{{ c2Active ? 'ONLINE' : 'STANDBY' }}</span>
                    <span class="cn-type-badge cn-trusted-badge">Trusted Cloud</span>
                  </div>
                  <div class="cn-name" :style="{color: c2Active ? '#34d399' : '#64748b'}">Trusted Cloud C2</div>
                  <div class="cn-subtitle">Trusted Cloud 2</div>
                  <div class="cn-duties">
                    <div class="cn-duty"><span class="cn-duty-dot" style="background:#34d399"></span>Physically isolated private key (SK) custody</div>
                    <div class="cn-duty"><span class="cn-duty-dot" style="background:#34d399"></span>Execute secure comparison protocol</div>
                    <div class="cn-duty"><span class="cn-duty-dot" style="background:#34d399"></span> Top-k result final decryption</div>
                  </div>
                  <div class="cn-key-tag cn-sk-tag">🛡️ Holds SK (Physical Isolation)</div>
                </div>
              </el-tooltip>
            </div>

            <!-- Sync index button -->
            <div class="sync-btn-row">
              <button
                class="sync-btn"
                :class="{ 'sync-btn-done': isNodesSynced, 'sync-btn-loading': isSyncing }"
                :disabled="isSyncing || isNodesSynced"
                @click="handleSyncIndex"
              >
                <span v-if="isSyncing" class="deploy-spinner"></span>
                <span v-else-if="isNodesSynced">✅ All grid index synced</span>
                <span v-else>🔄 Start compute cluster / provision containers</span>
              </button>
            </div>

            <!-- Cloud → Fog connection -->
            <div class="cloud-fog-connector">
              <div class="cfc-line"></div>
              <div class="cfc-label">Encrypted Task Distribution · Ciphertext Result Upload</div>
            </div>

            <!-- Spatial fog node network mapping -->
            <div class="fog-topology-wrap">
              <div class="fog-topology-title">
                <span class="fog-topo-label">Fog Spatial Topology</span>
                <span class="fog-topo-sub">Spatial Fog Node Network Mapping</span>
                <span class="fog-topo-duty">Duty: Store SLL · Text Similarity Calculation</span>
              </div>
              <div
                class="fog-node-grid"
                :style="{ '--cols': fogGridCols }"
              >
                <el-tooltip
                  v-for="(node, idx) in fogNodes"
                  :key="node.id"
                  effect="dark"
                  placement="top"
                  :show-after="80"
                >
                  <template #content>
                    <div class="fog-tooltip">
                      <div class="fog-tt-row"><span class="fog-tt-key">Node ID</span><span class="fog-tt-val">{{ node.id }}</span></div>
                      <div class="fog-tt-row"><span class="fog-tt-key">IP Address</span><span class="fog-tt-val">{{ node.ip }}</span></div>
                      <div class="fog-tt-row"><span class="fog-tt-key">Region X</span><span class="fog-tt-val">[{{ node.xMin }}, {{ node.xMax }}]</span></div>
                      <div class="fog-tt-row"><span class="fog-tt-key">Region Y</span><span class="fog-tt-val">[{{ node.yMin }}, {{ node.yMax }}]</span></div>
                      <div class="fog-tt-row"><span class="fog-tt-key">Index</span><span class="fog-tt-val" :class="litFogNodes.has(idx) ? 'fog-tt-green' : ''">{{ litFogNodes.has(idx) ? 'Local R-Tree Ready' : 'Standby' }}</span></div>
                      <div class="fog-tt-row"><span class="fog-tt-key">Records</span><span class="fog-tt-val">{{ node.records }} items</span></div>
                    </div>
                  </template>
                  <div
                    class="fog-node-cell"
                    :class="[
                      'fog-node-lv' + demoApp.fogLevel,
                      litFogNodes.has(idx) ? 'fog-node-lit' : 'fog-node-dim'
                    ]"
                  >
                    <span class="fog-node-pulse" :class="litFogNodes.has(idx) ? '' : 'fog-pulse-dim'"></span>
                    <span class="fog-node-id">{{ node.id }}</span>
                  </div>
                </el-tooltip>
              </div>

              <!-- Dynamic Statistics -->
              <div class="fog-stat-note">
                The global space has been securely partitioned into
                <span class="fog-stat-hl">{{ fogNodeCount }}</span>
                subspaces. All
                <span class="fog-stat-hl">{{ fogNodeCount }}</span>
                edge physical fog nodes are online and listening for ciphertext query routing.
              </div>
            </div>

            <div class="fog-academic-note">
              The system uses quadtree grid partitioning technology to map the global secure index (SGL) to physical fog nodes (SLL).
            </div>
          </div>

          <!-- ── Terminal user permission issuance ── -->
          <div class="auth-module">
            <div class="auth-module-header">
              <span class="auth-module-title">End User Authorization</span>
              <span class="auth-module-badge">Public Key Distribution</span>
              <span v-if="demoApp.userApplyStatus === 'pending'" class="auth-module-notify">
                <span class="notify-dot"></span>1 pending approval
              </span>
              <!-- Approval list status statistics -->
              <div class="auth-stats" v-if="demoApp.userApplyStatus !== 'none'">
                <span class="auth-stat-item">
                  <span class="auth-stat-dot" :style="{ background: demoApp.userApplyStatus === 'approved' ? '#34d399' : '#fbbf24' }"></span>
                  {{ demoApp.userApplyStatus === 'approved' ? 'Authorized' : 'Pending' }}
                </span>
              </div>
            </div>
            <div class="auth-module-body">

              <!-- ① No applications: empty list -->
              <div v-if="demoApp.userApplyStatus === 'none'" class="auth-empty">
                <span class="auth-empty-icon">📭</span>
                <span>No public key applications from end users yet</span>
              </div>

              <!-- ② / ③ Approval list table -->
              <template v-else>
                <!-- Table header -->
                <div class="auth-table-header">
                  <span class="ath-col ath-id">Terminal ID</span>
                  <span class="ath-col ath-time">Request Time</span>
                  <span class="ath-col ath-type">Request Type</span>
                  <span class="ath-col ath-status">Status</span>
                  <span class="ath-col ath-action">Action</span>
                </div>

                <!-- Record row -->
                <div class="auth-table-row" :class="{ 'atr-approved': demoApp.userApplyStatus === 'approved', 'atr-pending': demoApp.userApplyStatus === 'pending' }">
                  <!-- Terminal identifier -->
                  <div class="ath-col ath-id">
                    <span class="atr-client-icon">📱</span>
                    <div class="atr-client-info">
                      <span class="atr-client-name">Mobile Client-01</span>
                      <span class="atr-client-sub">{{ clientIp }}</span>
                    </div>
                  </div>

                  <!-- Request time -->
                  <div class="ath-col ath-time">
                    <span class="atr-time">{{ applyTimeDisplay }}</span>
                  </div>

                  <!-- Request type -->
                  <div class="ath-col ath-type">
                    <span class="atr-type-badge">Paillier Public Key Application</span>
                  </div>

                  <!-- Status -->
                  <div class="ath-col ath-status">
                    <span v-if="demoApp.userApplyStatus === 'pending'" class="atr-status-pending">
                      <span class="atr-status-dot"></span>Pending Approval
                    </span>
                    <span v-else class="atr-status-approved">
                      <span class="atr-status-dot atr-dot-approved"></span>Authorized
                    </span>
                  </div>

                  <!-- Actions -->
                  <div class="ath-col ath-action">
                    <template v-if="demoApp.userApplyStatus === 'pending'">
                      <el-button
                        type="success"
                        size="small"
                        :disabled="!demoApp.isKeyGenerated"
                        :title="!demoApp.isKeyGenerated ? 'Please generate key pair first' : ''"
                        @click="handleApproveKey"
                      >
                        Approve
                      </el-button>
                      <el-button type="danger" plain size="small" @click="handleRejectKey">Reject</el-button>
                    </template>
                    <template v-else>
                      <span class="atr-approve-time">{{ approveTimeDisplay }}</span>
                      <el-button type="warning" plain size="small" @click="handleRevokeKey">Revoke</el-button>
                    </template>
                  </div>
                </div>

                <!-- Key not generated warning -->
                <div class="arc-tip" v-if="demoApp.userApplyStatus === 'pending' && !demoApp.isKeyGenerated">
                  ⚠️ Please generate key pair above before approving public key application
                </div>

                <!-- Approved: TLS distribution success prompt -->
                <div v-if="demoApp.userApplyStatus === 'approved'" class="auth-tls-bar">
                  <span class="tls-icon">🔒</span>
                  <span class="tls-text">Public key (PK) has been distributed to query terminal via TLS secure channel · End-to-end encrypted transmission completed</span>
                  <span class="tls-badge">TLS 1.3</span>
                </div>
              </template>

            </div>
          </div>
        </section>

        <!-- Module 2: Safe Zone Settings -->
        <section v-show="activeSection === 'safezone'" class="config-section">
          <div class="section-header">
            <h2 class="section-title">Safe Zone Settings</h2>
            <span class="section-badge">Continuous Query Optimization</span>
          </div>

          <div class="form-grid">
            <el-form label-position="top" class="config-form">
              <el-form-item :label="`Protection Radius: ${cfg.safeZoneRadius} m`">
                <el-slider v-model="cfg.safeZoneRadius" :min="500" :max="2000" :step="100" :marks="radiusMarks" show-stops />
              </el-form-item>

              <el-form-item :label="`Location Update Interval: ${cfg.updateInterval} ms`">
                <el-slider v-model="cfg.updateInterval" :min="1000" :max="10000" :step="500" :marks="intervalMarks" show-stops />
              </el-form-item>

              <el-form-item label="Simulate Movement">
                <div class="switch-row">
                  <el-switch v-model="cfg.simulateMovement" @change="handleSimulateToggle" />
                  <span class="switch-desc">When enabled, automatically offset query point every {{ cfg.updateInterval }} ms</span>
                </div>
              </el-form-item>

              <el-form-item label="Hit Statistics">
                <div class="hit-counters">
                  <div class="hc-item hc-hit">
                    <span class="hc-num">{{ hitCount }}</span>
                    <span class="hc-label">Hits</span>
                  </div>
                  <div class="hc-item hc-miss">
                    <span class="hc-num">{{ missCount }}</span>
                    <span class="hc-label">Misses</span>
                  </div>
                  <div class="hc-item hc-rate">
                    <span class="hc-num">{{ hitCount + missCount > 0 ? Math.round(hitCount / (hitCount + missCount) * 100) : '—' }}%</span>
                    <span class="hc-label">Hit Rate</span>
                  </div>
                </div>
              </el-form-item>
            </el-form>

            <!-- Dynamic Safe Zone map -->
            <div class="safezone-visual">
              <div class="sv-title">Safe Zone Dynamic Preview</div>
              <div class="sv-map-wrap">
                <svg viewBox="0 0 240 200" class="sv-map">
                  <!-- Background -->
                  <rect width="240" height="200" fill="#0f172a" rx="10"/>
                  <g stroke="#1e293b" stroke-width="0.5">
                    <line v-for="x in 12" :key="'vl'+x" :x1="x*20" y1="0" :x2="x*20" y2="200"/>
                    <line v-for="y in 10" :key="'hl'+y" x1="0" :y1="y*20" x2="240" :y2="y*20"/>
                  </g>
                  <!-- Pulse wave -->
                  <circle cx="120" cy="100" :r="szRadius * 1.3" fill="none"
                    :stroke="safeZoneHit ? '#34d399' : '#f87171'" stroke-width="1"
                    :opacity="pulseOpacity" />
                  <!-- Safe Zone circle -->
                  <circle cx="120" cy="100" :r="szRadius"
                    :fill="safeZoneHit ? 'rgba(52,211,153,0.08)' : 'rgba(248,113,113,0.08)'"
                    :stroke="safeZoneHit ? '#34d399' : '#f87171'"
                    stroke-width="1.5" stroke-dasharray="5 3"/>
                  <!-- Radius annotation line -->
                  <line x1="120" y1="100" :x2="120 + szRadius" y2="100"
                    stroke="#38bdf8" stroke-width="1" stroke-dasharray="2 2" opacity="0.6"/>
                  <text :x="120 + szRadius / 2" y="95" font-size="9" fill="#38bdf8" text-anchor="middle">{{ cfg.safeZoneRadius }}m</text>
                  <!-- History track -->
                  <polyline v-if="trail.length > 1"
                    :points="trail.map(p => `${120+p.x},${100+p.y}`).join(' ')"
                    fill="none" stroke="#38bdf8" stroke-width="1" opacity="0.4"/>
                  <!-- Query point animation -->
                  <circle :cx="120 + previewDot.x" :cy="100 + previewDot.y" r="8"
                    fill="rgba(59,130,246,0.2)" class="dot-pulse"/>
                  <circle :cx="120 + previewDot.x" :cy="100 + previewDot.y" r="5"
                    fill="#3b82f6"/>
                  <!-- Center point -->
                  <circle cx="120" cy="100" r="4" fill="#ef4444"/>
                  <circle cx="120" cy="100" r="8" fill="none" stroke="#ef4444" stroke-width="1" opacity="0.5"/>
                  <!-- Status text -->
                  <rect x="4" y="4" width="80" height="18" rx="4"
                    :fill="safeZoneHit ? 'rgba(52,211,153,0.2)' : 'rgba(248,113,113,0.2)'"/>
                  <text x="10" y="16" font-size="9" :fill="safeZoneHit ? '#34d399' : '#f87171'" font-weight="bold">
                    {{ safeZoneHit ? '✓ CACHE HIT' : '✗ FULL QUERY' }}
                  </text>
                  <!-- Distance annotation -->
                  <text x="236" y="196" font-size="8" fill="#475569" text-anchor="end">dist: {{ distFromCenter }}m</text>
                </svg>
              </div>
            </div>
          </div>
        </section>

        <!-- Module 3: Weight Strategy -->
        <section v-show="activeSection === 'weight'" class="config-section">
          <div class="section-header">
            <h2 class="section-title">Weight Strategy</h2>
            <span class="section-badge">Scoring Model</span>
          </div>

          <div class="form-grid">
            <el-form label-position="top" class="config-form">
              <el-form-item label="Spatial / Text Weight (alpha)">
                <WeightSlider v-model="cfg.alpha" />
              </el-form-item>

              <el-form-item label="Current Weight Distribution">
                <div class="weight-display">
                  <div class="weight-item" style="--c:#409eff">
                    <div class="weight-bar" :style="{ width: cfg.alpha * 100 + '%' }"></div>
                    <span>Spatial Weight α = {{ cfg.alpha.toFixed(2) }}</span>
                  </div>
                  <div class="weight-item" style="--c:#67c23a">
                    <div class="weight-bar" :style="{ width: (1 - cfg.alpha) * 100 + '%' }"></div>
                    <span>Text Weight (1-α) = {{ (1 - cfg.alpha).toFixed(2) }}</span>
                  </div>
                </div>
              </el-form-item>

              <el-form-item label="Top-3 Result Ranking Preview">
                <div class="ranking-preview">
                  <div v-for="(poi, idx) in rankedPreview" :key="poi.name" class="rank-row">
                    <span class="rank-badge" :class="'rank-' + (idx + 1)">#{{ idx + 1 }}</span>
                    <div class="rank-body">
                      <span class="rank-name">{{ poi.name }}</span>
                      <div class="rank-scores">
                        <el-progress :percentage="Math.round(poi.finalScore * 100)" :stroke-width="6" :show-text="false" color="#409eff" style="flex:1" />
                        <span class="rank-score">{{ (poi.finalScore * 100).toFixed(1) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </el-form-item>
            </el-form>

            <!-- Weight visualization -->
            <div class="weight-visual">
              <div class="wv-title">Combined Score Simulation</div>
              <div class="wv-chart">
                <div v-for="poi in samplePOIs" :key="poi.name" class="wv-row">
                  <span class="wv-name">{{ poi.name }}</span>
                  <div class="wv-bars">
                    <div class="wv-bar-spatial" :style="{ width: poi.spatialScore * 100 + '%' }"></div>
                    <div class="wv-bar-text" :style="{ width: poi.textScore * 100 + '%' }"></div>
                    <div class="wv-bar-final" :style="{ width: (cfg.alpha * poi.spatialScore + (1-cfg.alpha) * poi.textScore) * 100 + '%' }"></div>
                  </div>
                  <span class="wv-score">{{ ((cfg.alpha * poi.spatialScore + (1-cfg.alpha) * poi.textScore) * 100).toFixed(0) }}</span>
                </div>
              </div>
              <div class="wv-legend">
                <span class="wv-leg-item"><span class="wv-dot" style="background:#409eff"></span>Spatial</span>
                <span class="wv-leg-item"><span class="wv-dot" style="background:#67c23a"></span>Text</span>
                <span class="wv-leg-item"><span class="wv-dot" style="background:#f59e0b"></span>Combined</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <!-- ── Right column: Real-time preview summary ── -->
      <aside class="config-preview">
        <div class="preview-header">Real-time Preview</div>
        <div class="preview-summary">
          <div class="ps-item">
            <span class="ps-key">Key Length</span>
            <span class="ps-val" :style="{ color: estimateColor }">{{ cfg.keySize }} bit</span>
          </div>
          <div class="ps-item">
            <span class="ps-key">Encryption Time Est.</span>
            <span class="ps-val">{{ cfg.estimateEncryptionMs() }} ms</span>
          </div>
          <div class="ps-item">
            <span class="ps-key">Key Status</span>
            <span class="ps-val" :style="{ color: cfg.keysGenerated ? '#34d399' : '#f59e0b' }">{{ cfg.keysGenerated ? 'Generated' : 'Not Generated' }}</span>
          </div>
          <div class="ps-divider"></div>
          <div class="ps-item">
            <span class="ps-key">Safe Zone Radius</span>
            <span class="ps-val">{{ cfg.safeZoneRadius }} m</span>
          </div>
          <div class="ps-item">
            <span class="ps-key">Update Interval</span>
            <span class="ps-val">{{ cfg.updateInterval }} ms</span>
          </div>
          <div class="ps-item">
            <span class="ps-key">Simulated Movement</span>
            <span class="ps-val" :style="{ color: cfg.simulateMovement ? '#34d399' : '#64748b' }">{{ cfg.simulateMovement ? 'Running' : 'Stopped' }}</span>
          </div>
          <div class="ps-item">
            <span class="ps-key">Hit Status</span>
            <span class="ps-val" :style="{ color: safeZoneHit ? '#34d399' : '#f87171' }">{{ safeZoneHit ? '✓ Hit' : '✗ Miss' }}</span>
          </div>
          <div class="ps-divider"></div>
          <div class="ps-item">
            <span class="ps-key">Spatial Weight α</span>
            <span class="ps-val" style="color:#409eff">{{ cfg.alpha.toFixed(2) }}</span>
          </div>
          <div class="ps-item">
            <span class="ps-key">Text Weight 1-α</span>
            <span class="ps-val" style="color:#67c23a">{{ (1 - cfg.alpha).toFixed(2) }}</span>
          </div>
          <div class="ps-divider"></div>
          <div class="ps-item">
            <span class="ps-key">Fog Level</span>
            <span class="ps-val" style="color:#818cf8">Lv.{{ demoApp.fogLevel }} · {{ demoApp.fogLevel === 1 ? '4' : demoApp.fogLevel === 2 ? '16' : '64' }} cells</span>
          </div>
          <div class="ps-item">
            <span class="ps-key">Terminal Auth</span>
            <span class="ps-val" :style="{ color: demoApp.userApplyStatus === 'approved' ? '#34d399' : demoApp.userApplyStatus === 'pending' ? '#fbbf24' : '#f87171' }">
              {{ demoApp.userApplyStatus === 'approved' ? '✓ Authorized' : demoApp.userApplyStatus === 'pending' ? '⏳ Pending' : '✗ Unauthorized' }}
            </span>
          </div>
        </div>

        <!-- Real-time pulse indicator -->
        <div class="preview-pulse">
          <div class="pulse-ring" :class="{ 'pulse-active': cfg.simulateMovement }"></div>
          <div class="pulse-dot" :class="safeZoneHit ? 'pulse-hit' : 'pulse-miss'"></div>
          <span class="pulse-label">{{ cfg.simulateMovement ? (safeZoneHit ? 'CACHE HIT' : 'QUERYING') : 'IDLE' }}</span>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElLoading, ElNotification } from 'element-plus';
import { Check, Lock, Location, DataLine, Download } from '@element-plus/icons-vue';
import WeightSlider from '@/components/query/WeightSlider.vue';
import { useConfigStore } from '@/stores/config.store';
import { useQueryStore } from '@/stores/query.store';
import { useDemoAppStore } from '@/stores/useDemoStore';

const router = useRouter();
const cfg = useConfigStore();
const queryStore = useQueryStore();
const demoApp = useDemoAppStore();

const activeSection = ref<'crypto' | 'safezone' | 'weight'>('crypto');
const navItems = [
  { key: 'crypto',   label: 'Encryption Config',       icon: Lock },
  { key: 'safezone', label: 'Safe Zone Settings', icon: Location },
  { key: 'weight',   label: 'Weight Strategy',    icon: DataLine },
] as const;

// ── Encryption module ──
const generatingKey = ref(false);

// ── Key deployment state machine ──
type DeployStatus = 'idle' | 'deploying' | 'done';
const deployStatus  = ref<DeployStatus>('idle');
const isDeploying   = ref(false);
const pkDeployed    = ref(false);
const skDeployed    = ref(false);
const deployFlowing = ref(false); // Control connection line flow animation

async function handleDeployKeys() {
  if (!cfg.privateKeyRaw || isDeploying.value || deployStatus.value === 'done') return;
  isDeploying.value  = true;
  deployStatus.value = 'deploying';
  deployFlowing.value = true;

  // Step 1
  ElNotification({ title: 'Cluster Deployment', message: 'Establishing secure handshake with main cloud C1...', type: 'info', duration: 2200, position: 'bottom-right' });
  await delay(1400);

  // Step 2: PK distribution
  pkDeployed.value = true;
  ElNotification({ title: 'Cluster Deployment', message: '✓ Public Key (PK) synchronized to C1 and all fog nodes', type: 'success', duration: 2500, position: 'bottom-right' });
  await delay(1200);

  // Step 3: SK isolation
  ElNotification({ title: 'Cluster Deployment', message: 'Connecting to C2 trusted secure zone (TEE Enclave)...', type: 'info', duration: 2000, position: 'bottom-right' });
  await delay(1400);
  skDeployed.value = true;
  ElNotification({ title: 'Cluster Deployment', message: '🛡️ Private key (SK) has been physically isolated and local memory copy destroyed', type: 'success', duration: 3000, position: 'bottom-right' });
  await delay(800);

  // Complete
  deployFlowing.value = false;
  deployStatus.value  = 'done';
  isDeploying.value   = false;
  ElNotification({ title: 'Cluster Deployment', message: '✅ Cluster key deployment complete, system in secure operation mode', type: 'success', duration: 3500, position: 'bottom-right' });
}

// ── Node sync status ──
const isSyncing      = ref(false);
const isNodesSynced  = ref(false);
const c1Active       = ref(false);
const c2Active       = ref(false);
// Activated fog node indices
const litFogNodes    = ref<Set<number>>(new Set());
let   syncTimers: ReturnType<typeof setTimeout>[] = [];

async function handleSyncIndex() {
  if (isSyncing.value || isNodesSynced.value) return;
  isSyncing.value = true;
  litFogNodes.value = new Set();
  c1Active.value = false;
  c2Active.value = false;

  ElNotification({ title: 'Index Sync', message: 'Initializing cluster, connecting to main cloud C1...', type: 'info', duration: 2000, position: 'bottom-right' });
  await delay(900);
  c1Active.value = true;
  ElNotification({ title: 'Index Sync', message: '✓ C1 online, Secure Global Index (SGL) loaded', type: 'success', duration: 2200, position: 'bottom-right' });
  await delay(600);
  c2Active.value = true;
  ElNotification({ title: 'Index Sync', message: '🛡️ C2 trusted node online, private key custody ready', type: 'success', duration: 2000, position: 'bottom-right' });
  await delay(400);

  // Cascade light up fog nodes
  const count = fogNodeCount.value;
  for (let i = 0; i < count; i++) {
    const t = setTimeout(() => {
      litFogNodes.value = new Set([...litFogNodes.value, i]);
      if (i === count - 1) {
        isSyncing.value     = false;
        isNodesSynced.value = true;
        ElNotification({ title: 'Index Sync', message: `✅ All ${count} fog node SLL index sync completed, system ready`, type: 'success', duration: 3500, position: 'bottom-right' });
      }
    }, i * (count <= 4 ? 400 : count <= 16 ? 160 : 60));
    syncTimers.push(t);
  }
}

function resetCluster() {
  deployStatus.value  = 'idle';
  pkDeployed.value    = false;
  skDeployed.value    = false;
  deployFlowing.value = false;
  isDeploying.value   = false;
  isSyncing.value     = false;
  isNodesSynced.value = false;
  c1Active.value      = false;
  c2Active.value      = false;
  litFogNodes.value   = new Set();
  syncTimers.forEach(clearTimeout);
  syncTimers = [];
}

function delay(ms: number) { return new Promise<void>(r => setTimeout(r, ms)); }

async function handleGenerateKey() {
  generatingKey.value = true;
  const loading = ElLoading.service({
    lock: true,
    text: `Generating ${cfg.keySize}-bit Paillier key pair, please wait...`,
    background: 'rgba(0,0,0,0.6)',
  });
  try {
    await cfg.generateKeyPair();
    ElMessage.success(`Key pair generated successfully! Fingerprint: ${cfg.keyDigest}  Time: ${cfg.keyGenTimeMs} ms`);
    demoApp.markKeyGenerated();
  } catch (e: any) {
    ElMessage.error(`Key generation failed: ${e?.message ?? 'Network error, please ensure backend is running'}`);
  } finally {
    loading.close();
    generatingKey.value = false;
  }
}

function handleDownloadPrivateKey() {
  try {
    cfg.downloadPrivateKey();
    ElMessage.success('Private key downloaded, please keep it safe');
  } catch (e: any) {
    ElMessage.error(`Download failed: ${e?.message}`);
  }
}

// ── Terminal user permission approval ──
const applyTime   = ref<Date | null>(null);
const approveTime = ref<Date | null>(null);
const clientIp    = ref('192.168.1.' + Math.floor(Math.random() * 200 + 10));

const applyTimeDisplay = computed(() => {
  if (!applyTime.value) return '—';
  return applyTime.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
});
const approveTimeDisplay = computed(() => {
  if (!approveTime.value) return '—';
  return `${approveTime.value.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })} Authorized`;
});

// Listen for userApplyStatus changes to pending, record application time
watch(() => demoApp.userApplyStatus, (status, oldStatus) => {
  if (status === 'pending' && oldStatus === 'none') {
    applyTime.value = new Date();
    approveTime.value = null;
  }
});

function handleApproveKey() {
  demoApp.reviewKeyRequest(true);
  approveTime.value = new Date();
  ElMessage({
    message: 'Public Key (PK) has been sent to query terminal via TLS secure channel',
    type: 'success',
    duration: 3500,
    showClose: true,
  });
}
function handleRejectKey() {
  demoApp.reviewKeyRequest(false);
  applyTime.value = null;
  ElMessage.warning('Public key request rejected');
}
function handleRevokeKey() {
  demoApp.revokeAccess();
  applyTime.value = null;
  approveTime.value = null;
  ElMessage.info('Terminal user public key authorization revoked');
}

const estimateColor = computed(() => {
  const ms = cfg.estimateEncryptionMs();
  if (ms < 50) return '#34d399';
  if (ms < 200) return '#f59e0b';
  return '#f87171';
});

const keySizePercent = computed(() => {
  if (cfg.keySize <= 512) return 33;
  if (cfg.keySize <= 1024) return 66;
  return 100;
});

const digestDisplay = computed(() => {
  const d = cfg.keyDigest;
  if (!d) return '—';
  return d.length > 12 ? `${d.slice(0, 8)}…${d.slice(-4)}` : d;
});

// ── Safe Zone module ──
const radiusMarks = { 500: '500m', 1000: '1km', 1500: '1.5km', 2000: '2km' };
const intervalMarks = { 1000: '1s', 5000: '5s', 10000: '10s' };

const previewDot = ref({ x: 0, y: 0 });
const trail = ref<{ x: number; y: number }[]>([]);
const hitCount = ref(0);
const missCount = ref(0);
const pulseOpacity = ref(0.8);
let moveTimer: ReturnType<typeof setInterval> | null = null;
let pulseTimer: ReturnType<typeof setInterval> | null = null;

function handleSimulateToggle(enabled: boolean) {
  if (moveTimer) { clearInterval(moveTimer); moveTimer = null; }
  if (pulseTimer) { clearInterval(pulseTimer); pulseTimer = null; }
  if (enabled) {
    moveTimer = setInterval(() => {
      const nx = Math.round((Math.random() - 0.5) * cfg.safeZoneRadius * 0.6);
      const ny = Math.round((Math.random() - 0.5) * cfg.safeZoneRadius * 0.6);
      previewDot.value = { x: nx, y: ny };
      trail.value.push({ x: nx, y: ny });
      if (trail.value.length > 12) trail.value.shift();
      const dist = Math.sqrt(nx ** 2 + ny ** 2) / 90 * 2000;
      if (dist <= cfg.safeZoneRadius) hitCount.value++;
      else missCount.value++;
    }, cfg.updateInterval);
    pulseTimer = setInterval(() => {
      pulseOpacity.value = pulseOpacity.value > 0.1 ? pulseOpacity.value - 0.15 : 0.8;
    }, 200);
  } else {
    previewDot.value = { x: 0, y: 0 };
    trail.value = [];
  }
}

const szRadius = computed(() => Math.round((cfg.safeZoneRadius / 2000) * 90));
const distFromCenter = computed(() => {
  const px = Math.sqrt(previewDot.value.x ** 2 + previewDot.value.y ** 2);
  return Math.round((px / 90) * 2000);
});
const safeZoneHit = computed(() => distFromCenter.value <= cfg.safeZoneRadius);

// ── Fog node topology module ──
const fogNodeCount = computed(() =>
  demoApp.fogLevel === 1 ? 4 : demoApp.fogLevel === 2 ? 16 : 64
);
const fogGridCols = computed(() =>
  demoApp.fogLevel === 1 ? 2 : demoApp.fogLevel === 2 ? 4 : 8
);

// Generate fog node data (with fake IP and area boundaries)
const fogNodes = computed(() => {
  const count = fogNodeCount.value;
  const cols  = fogGridCols.value;
  const step  = Math.round(10000 / cols);
  // Fixed random seed effect: use index to generate stable pseudo-random numbers
  function seededRand(seed: number, min: number, max: number) {
    const x = Math.sin(seed + 1) * 10000;
    return min + Math.round((x - Math.floor(x)) * (max - min));
  }
  return Array.from({ length: count }, (_, i) => {
    const row = Math.floor(i / cols);
    const col = i % cols;
    const idNum = String(i + 1).padStart(2, '0');
    return {
      id: `FS-${idNum}`,
      ip: `192.168.${10 + row}.${col * 10 + seededRand(i * 7, 1, 9)}`,
      xMin: col * step,
      xMax: (col + 1) * step,
      yMin: row * step,
      yMax: (row + 1) * step,
      records: seededRand(i * 13, 120, 9800),
    };
  });
});

// ── Weight module ──
const samplePOIs = [
  { name: 'Nearby Café',       spatialScore: 0.95, textScore: 0.45 },
  { name: 'Central Library',   spatialScore: 0.55, textScore: 0.92 },
  { name: 'Community Hospital', spatialScore: 0.78, textScore: 0.68 },
  { name: 'Supermarket',       spatialScore: 0.40, textScore: 0.85 },
  { name: 'City Park',         spatialScore: 0.88, textScore: 0.35 },
];

const rankedPreview = computed(() => {
  return samplePOIs
    .map(p => ({ ...p, finalScore: cfg.alpha * p.spatialScore + (1 - cfg.alpha) * p.textScore }))
    .sort((a, b) => b.finalScore - a.finalScore)
    .slice(0, 3);
});

// ── Global operations ──
function handleSave() { cfg.save(); ElMessage.success('Configuration saved'); }
function handleRestore() {
  cfg.restoreDefaults();
  previewDot.value = { x: 0, y: 0 };
  trail.value = [];
  hitCount.value = 0;
  missCount.value = 0;
  if (moveTimer) { clearInterval(moveTimer); moveTimer = null; }
  if (pulseTimer) { clearInterval(pulseTimer); pulseTimer = null; }
  ElMessage.info('Configuration restored to defaults');
}

onMounted(async () => { cfg.load(); await cfg.syncKeyStatus(); });
onUnmounted(() => {
  if (moveTimer) clearInterval(moveTimer);
  if (pulseTimer) clearInterval(pulseTimer);
  syncTimers.forEach(clearTimeout);
});
</script>

<style scoped>
.config-view { height: 100vh; display: flex; flex-direction: column; background: #0d1117; overflow: hidden; }

/* ── Top bar ── */
.config-topbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 28px; background: #131720; border-bottom: 1px solid #1e293b; flex-shrink: 0; }
.topbar-left { display: flex; align-items: baseline; gap: 14px; }
.topbar-title { font-size: 20px; font-weight: 700; color: #f1f5f9; }
.topbar-subtitle { font-size: 13px; color: #475569; }
.topbar-actions { display: flex; gap: 8px; }

/* ── Main ── */
.config-body { flex: 1; display: flex; min-height: 0; overflow: hidden; }

/* ── Left column ── */
.config-nav { width: 150px; flex-shrink: 0; background: #131720; border-right: 1px solid #1e293b; padding: 12px 0; display: flex; flex-direction: column; gap: 2px; overflow-y: auto; }
.nav-item { display: flex; align-items: center; gap: 8px; padding: 10px 16px; cursor: pointer; font-size: 13px; color: #64748b; border-left: 3px solid transparent; transition: all 0.15s; }
.nav-item:hover { background: rgba(56,189,248,0.06); color: #94a3b8; }
.nav-item { display: flex; align-items: center; gap: 8px; padding: 10px 16px; cursor: pointer; font-size: 14px; color: #64748b; border-left: 3px solid transparent; transition: all 0.15s; }
.nav-item:hover { background: rgba(56,189,248,0.06); color: #94a3b8; }
.nav-item.active { background: rgba(56,189,248,0.1); color: #38bdf8; border-left-color: #38bdf8; font-weight: 600; }
.nav-icon { font-size: 16px; flex-shrink: 0; }
.nav-label { white-space: nowrap; }

/* ── Middle column ── */
.config-main { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 24px 28px 40px; min-width: 0; min-height: 0; }
.config-section { min-height: min-content; }
.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 22px; padding-bottom: 14px; border-bottom: 1px solid #1e293b; }
.section-title { font-size: 18px; font-weight: 700; color: #f1f5f9; margin: 0; }
.section-badge { font-size: 12px; color: #38bdf8; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.2); border-radius: 4px; padding: 3px 10px; }

/* Two-column layout */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }

:deep(.config-form .el-form-item) { margin-bottom: 22px; }
:deep(.config-form .el-form-item__label) { color: #94a3b8; font-size: 13px; padding-bottom: 6px; }
.field-hint { margin-top: 6px; font-size: 13px; color: #475569; }

/* Encryption module */
.estimate-bar { display: flex; align-items: center; gap: 10px; }
.estimate-label { font-size: 14px; font-variant-numeric: tabular-nums; color: #64748b; min-width: 64px; text-align: right; }
.key-status { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.key-time { font-size: 13px; color: #64748b; }

/* Key visualization */
.crypto-visual { background: #131720; border: 1px solid #1e293b; border-radius: 10px; padding: 16px; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.cv-title { font-size: 13px; color: #64748b; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
.cv-ring-wrap { width: 140px; height: 140px; }
.cv-ring { width: 100%; height: 100%; }
.cv-levels { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.cv-level { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #475569; transition: color 0.3s; }
.cv-level.active { color: #94a3b8; }
.cv-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; opacity: 0.3; }
.cv-level.active .cv-dot { opacity: 1; }

/* Safe Zone module */
.hit-counters { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
.hc-item { display: flex; flex-direction: column; align-items: center; padding: 10px 6px; background: #131720; border-radius: 8px; border: 1px solid #1e293b; }
.hc-num { font-size: 24px; font-weight: 700; font-variant-numeric: tabular-nums; }
.hc-label { font-size: 12px; color: #475569; margin-top: 2px; }
.hc-hit .hc-num { color: #34d399; }
.hc-miss .hc-num { color: #f87171; }
.hc-rate .hc-num { color: #38bdf8; }
.switch-row { display: flex; align-items: center; gap: 10px; }
.switch-desc { font-size: 13px; color: #64748b; line-height: 1.4; }

/* Safe Zone visualization */
.safezone-visual { background: #131720; border: 1px solid #1e293b; border-radius: 10px; padding: 12px; }
.sv-title { font-size: 13px; color: #64748b; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
.sv-map-wrap { width: 100%; }
.sv-map { width: 100%; height: auto; border-radius: 8px; }
@keyframes dotPulse { 0%,100%{r:8;opacity:0.3} 50%{r:12;opacity:0.6} }
.dot-pulse { animation: dotPulse 1.2s ease-in-out infinite; }

/* Weight module */
.weight-display { display: flex; flex-direction: column; gap: 8px; }
.weight-item { display: flex; flex-direction: column; gap: 4px; }
.weight-item span { font-size: 13px; color: #64748b; }
.weight-bar { height: 8px; background: var(--c); border-radius: 4px; transition: width 0.3s ease; min-width: 4px; }
.ranking-preview { display: flex; flex-direction: column; gap: 6px; }
.rank-row { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: #131720; border-radius: 6px; border: 1px solid #1e293b; }
.rank-badge { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; color: #fff; }
.rank-1 { background: #f59e0b; } .rank-2 { background: #94a3b8; } .rank-3 { background: #b45309; }
.rank-body { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.rank-name { font-size: 13px; font-weight: 500; color: #94a3b8; }
.rank-scores { display: flex; align-items: center; gap: 6px; }
.rank-score { font-size: 12px; font-variant-numeric: tabular-nums; color: #64748b; min-width: 28px; text-align: right; }

/* Weight visualization */
.weight-visual { background: #131720; border: 1px solid #1e293b; border-radius: 10px; padding: 14px; }
.wv-title { font-size: 13px; color: #64748b; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 10px; }
.wv-chart { display: flex; flex-direction: column; gap: 6px; }
.wv-row { display: flex; align-items: center; gap: 8px; }
.wv-name { font-size: 12px; color: #64748b; width: 68px; flex-shrink: 0; }
.wv-bars { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.wv-bar-spatial { height: 4px; background: #409eff; border-radius: 2px; transition: width 0.3s; min-width: 2px; opacity: 0.6; }
.wv-bar-text { height: 4px; background: #67c23a; border-radius: 2px; transition: width 0.3s; min-width: 2px; opacity: 0.6; }
.wv-bar-final { height: 5px; background: #f59e0b; border-radius: 2px; transition: width 0.3s; min-width: 2px; }
.wv-score { font-size: 12px; color: #f59e0b; font-variant-numeric: tabular-nums; min-width: 24px; text-align: right; }
.wv-legend { display: flex; gap: 12px; margin-top: 10px; }
.wv-leg-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #64748b; }
.wv-dot { width: 8px; height: 8px; border-radius: 50%; }

/* ── Right column ── */
.config-preview { width: 220px; flex-shrink: 0; background: #131720; border-left: 1px solid #1e293b; display: flex; flex-direction: column; overflow-y: auto; }
.preview-header { padding: 13px 16px 9px; font-size: 13px; font-weight: 700; color: #64748b; letter-spacing: 1px; text-transform: uppercase; border-bottom: 1px solid #1e293b; flex-shrink: 0; }
.preview-summary { padding: 10px 14px; display: flex; flex-direction: column; gap: 2px; }
.ps-item { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid #1e293b; }
.ps-key { font-size: 12px; color: #475569; }
.ps-val { font-size: 13px; font-weight: 600; color: #94a3b8; font-variant-numeric: tabular-nums; }
.ps-divider { height: 1px; background: #1e293b; margin: 4px 0; }

/* Pulse indicator */
.preview-pulse { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 16px; margin-top: auto; border-top: 1px solid #1e293b; }
.pulse-ring { width: 48px; height: 48px; border-radius: 50%; border: 2px solid #1e293b; position: relative; }
.pulse-ring.pulse-active { animation: pulseRing 1.5s ease-in-out infinite; border-color: #38bdf8; }
@keyframes pulseRing { 0%,100%{box-shadow:0 0 0 0 rgba(56,189,248,0.4)} 50%{box-shadow:0 0 0 10px rgba(56,189,248,0)} }
.pulse-dot { width: 16px; height: 16px; border-radius: 50%; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); margin-top: -32px; }
.pulse-hit { background: #34d399; box-shadow: 0 0 8px #34d399; }
.pulse-miss { background: #f87171; box-shadow: 0 0 8px #f87171; }
.pulse-label { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #64748b; }

@media (max-width: 1100px) { .form-grid { grid-template-columns: 1fr; } }
@media (max-width: 800px) { .config-preview { display: none; } }

/* ══════════════════════════════════════════════
   Key Flow Panel
══════════════════════════════════════════════ */
.key-flow-panel {
  width: 100%;
  background: #060d1a;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  overflow: hidden;
  padding: 14px;
}
.kf-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #38bdf8;
  text-transform: uppercase;
  margin-bottom: 12px;
  font-family: 'JetBrains Mono', monospace;
}
.kf-title-icon { font-size: 13px; }
.kf-items { display: flex; flex-direction: column; gap: 8px; }
.kf-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid;
}
.kf-item-pk {
  background: rgba(56,189,248,0.05);
  border-color: rgba(56,189,248,0.2);
}
.kf-item-sk {
  background: rgba(52,211,153,0.05);
  border-color: rgba(52,211,153,0.2);
}
.kf-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
  width: 36px;
}
.kf-key-badge {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1px;
}
.kf-pk { background: rgba(56,189,248,0.2); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); }
.kf-sk { background: rgba(52,211,153,0.2); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.kf-key-label { font-size: 9px; color: #475569; }
.kf-arrow { flex-shrink: 0; opacity: 0.8; }
.kf-right { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.kf-dest-row { display: flex; align-items: center; gap: 6px; }
.kf-dest { font-size: 12px; font-weight: 700; color: #94a3b8; }
.kf-dest-secure { color: #34d399; }
.kf-shield { font-size: 14px; }
.kf-desc { font-size: 10px; color: #475569; line-height: 1.5; }
.kf-footer {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #0f1e35;
  font-size: 10px;
  color: #334155;
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
}

/* Key flow header row */
.kf-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 10px;
}

/* Status tag */
.kf-status-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.kf-tag-pending {
  background: rgba(100,116,139,0.15);
  color: #64748b;
  border: 1px solid rgba(100,116,139,0.2);
}
.kf-tag-synced {
  background: rgba(56,189,248,0.15);
  color: #38bdf8;
  border: 1px solid rgba(56,189,248,0.25);
  animation: tagGlow 1.5s ease-in-out 3;
}
.kf-tag-locked {
  background: rgba(52,211,153,0.15);
  color: #34d399;
  border: 1px solid rgba(52,211,153,0.25);
  animation: tagGlow 1.5s ease-in-out 3;
}
@keyframes tagGlow {
  0%,100% { box-shadow: none; }
  50%      { box-shadow: 0 0 8px rgba(52,211,153,0.5); }
}

/* kf-item activated state */
.kf-item-active {
  border-color: rgba(56,189,248,0.4) !important;
  background: rgba(56,189,248,0.08) !important;
}
.kf-item-active-sk {
  border-color: rgba(52,211,153,0.4) !important;
  background: rgba(52,211,153,0.08) !important;
}

/* Arrow flow animation */
.kf-arrow-flowing svg line {
  animation: dashFlow 0.6s linear infinite;
}
.kf-arrow-flowing-sk svg line {
  animation: dashFlowGreen 0.6s linear infinite;
}
@keyframes dashFlow {
  to { stroke-dashoffset: -10; }
}
@keyframes dashFlowGreen {
  to { stroke-dashoffset: -10; }
}

/* Deploy button */
.deploy-btn {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 7px 14px;
  border-radius: 7px;
  border: 1px solid;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'JetBrains Mono', monospace;
  white-space: nowrap;
  flex-shrink: 0;
}
.deploy-btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
}
.deploy-btn-ready {
  background: linear-gradient(135deg, rgba(56,189,248,0.15), rgba(129,140,248,0.15));
  border-color: rgba(56,189,248,0.4);
  color: #38bdf8;
  box-shadow: 0 0 12px rgba(56,189,248,0.15);
}
.deploy-btn-ready:hover {
  background: linear-gradient(135deg, rgba(56,189,248,0.25), rgba(129,140,248,0.25));
  box-shadow: 0 0 20px rgba(56,189,248,0.3);
  transform: translateY(-1px);
}
.deploy-btn-loading {
  background: rgba(251,191,36,0.1);
  border-color: rgba(251,191,36,0.3);
  color: #fbbf24;
  cursor: not-allowed;
}
.deploy-btn-done {
  background: rgba(52,211,153,0.1);
  border-color: rgba(52,211,153,0.3);
  color: #34d399;
  cursor: default;
}
.deploy-icon { font-size: 13px; }
.deploy-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(251,191,36,0.3);
  border-top-color: #fbbf24;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ══════════════════════════════════════════════
   Cloud Node Cards
══════════════════════════════════════════════ */
.cloud-nodes-row {
  display: flex;
  align-items: center;
  gap: 0;
  margin: 14px 16px 0;
  justify-content: center;
}
.cloud-node-card {
  flex: 1;
  max-width: 260px;
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  overflow: hidden;
}
.cloud-node-c1 {
  background: linear-gradient(135deg, rgba(56,189,248,0.07) 0%, rgba(30,41,59,0.6) 100%);
  border: 1px solid rgba(56,189,248,0.3);
}
.cloud-node-c2 {
  background: linear-gradient(135deg, rgba(52,211,153,0.07) 0%, rgba(30,41,59,0.6) 100%);
  border: 1px solid rgba(52,211,153,0.3);
}
.cn-header {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cn-online-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 6px #38bdf8;
  animation: fogPulse 1.2s ease-in-out infinite;
  flex-shrink: 0;
}
.cn-online-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
}
.cn-type-badge {
  margin-left: auto;
  font-size: 9px;
  color: #38bdf8;
  background: rgba(56,189,248,0.1);
  border: 1px solid rgba(56,189,248,0.2);
  border-radius: 3px;
  padding: 1px 5px;
  font-family: 'JetBrains Mono', monospace;
}
.cn-trusted-badge {
  color: #34d399;
  background: rgba(52,211,153,0.1);
  border-color: rgba(52,211,153,0.2);
}
.cn-name {
  font-size: 16px;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}
.cloud-node-c2 .cn-name { color: #34d399; }
.cn-subtitle {
  font-size: 10px;
  color: #475569;
  font-family: 'JetBrains Mono', monospace;
  margin-top: -4px;
}
.cn-duties {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 2px;
}
.cn-duty {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #64748b;
}
.cn-duty-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}
.cn-key-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  margin-top: 4px;
  font-family: 'JetBrains Mono', monospace;
  width: fit-content;
}
.cn-pk-tag {
  background: rgba(56,189,248,0.12);
  color: #38bdf8;
  border: 1px solid rgba(56,189,248,0.25);
}
.cn-sk-tag {
  background: rgba(52,211,153,0.12);
  color: #34d399;
  border: 1px solid rgba(52,211,153,0.25);
}

/* Cloud node connector */
.cloud-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
  flex-shrink: 0;
}
.cloud-connector-label {
  font-size: 9px;
  color: #334155;
  white-space: nowrap;
  font-family: 'JetBrains Mono', monospace;
}

/* Cloud node dynamic status */
.cn-dot-online {
  background: #38bdf8 !important;
  box-shadow: 0 0 6px #38bdf8 !important;
  animation: fogPulse 1s ease-in-out infinite !important;
}
.cn-dot-online-c2 {
  background: #34d399 !important;
  box-shadow: 0 0 6px #34d399 !important;
  animation: fogPulse 1s ease-in-out infinite !important;
}
.cn-dot-standby {
  background: #334155 !important;
  box-shadow: none !important;
  animation: none !important;
}
.cn-standby {
  opacity: 0.5;
  filter: grayscale(0.6);
  transition: opacity 0.5s, filter 0.5s;
}
.cn-active {
  opacity: 1;
  filter: none;
  border-color: rgba(56,189,248,0.5) !important;
  box-shadow: 0 0 16px rgba(56,189,248,0.1);
  transition: all 0.5s;
}
.cn-active-c2 {
  opacity: 1;
  filter: none;
  border-color: rgba(52,211,153,0.5) !important;
  box-shadow: 0 0 16px rgba(52,211,153,0.1);
  transition: all 0.5s;
}

/* Sync button row */
.sync-btn-row {
  display: flex;
  justify-content: center;
  padding: 10px 16px 0;
}
.sync-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  border-radius: 8px;
  border: 1px solid rgba(129,140,248,0.35);
  background: rgba(129,140,248,0.08);
  color: #818cf8;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}
.sync-btn:hover:not(:disabled) {
  background: rgba(129,140,248,0.15);
  box-shadow: 0 0 14px rgba(129,140,248,0.2);
  transform: translateY(-1px);
}
.sync-btn-loading {
  color: #fbbf24 !important;
  border-color: rgba(251,191,36,0.3) !important;
  background: rgba(251,191,36,0.06) !important;
  cursor: not-allowed !important;
}
.sync-btn-done {
  color: #34d399 !important;
  border-color: rgba(52,211,153,0.3) !important;
  background: rgba(52,211,153,0.06) !important;
  cursor: default !important;
}

/* Fog node lit/standby */
.fog-node-lit {
  border-color: rgba(52,211,153,0.6) !important;
  background: rgba(52,211,153,0.08) !important;
  transition: all 0.3s ease;
}
.fog-node-dim {
  border-color: rgba(71,85,105,0.3) !important;
  background: rgba(15,23,42,0.5) !important;
  opacity: 0.5;
  transition: all 0.3s ease;
}
.fog-pulse-dim {
  background: #334155 !important;
  box-shadow: none !important;
  animation: none !important;
}

/* Cloud node tooltip */
.cn-tooltip {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 220px;
  font-family: 'JetBrains Mono', monospace;
}
.cnt-title {
  font-size: 11px;
  font-weight: 700;
  color: #38bdf8;
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(56,189,248,0.2);
  margin-bottom: 3px;
}
.cnt-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 11px;
}
.cnt-key { color: #64748b; flex-shrink: 0; }
.cnt-val { color: #cbd5e1; text-align: right; font-weight: 600; }

/* Cloud to fog connector */
.cloud-fog-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 16px 0;
}
.cfc-line {
  width: 1px;
  height: 20px;
  background: linear-gradient(180deg, #334155 0%, #1e3a5f 100%);
  position: relative;
}
.cfc-line::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: -3px;
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 6px solid #1e3a5f;
}
.cfc-label {
  font-size: 10px;
  color: #334155;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

/* Fog node duty tag */
.fog-topo-duty {
  font-size: 10px;
  color: #fbbf24;
  background: rgba(251,191,36,0.08);
  border: 1px solid rgba(251,191,36,0.2);
  border-radius: 4px;
  padding: 1px 7px;
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
}

/* ══════════════════════════════════════════════
   Approval List Table
══════════════════════════════════════════════ */
.auth-stats {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
}
.auth-stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: #64748b;
}
.auth-stat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.auth-table-header {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  background: #0a0f1a;
  border-radius: 6px 6px 0 0;
  border: 1px solid #1e293b;
  border-bottom: none;
  gap: 0;
}
.ath-col {
  font-size: 10px;
  font-weight: 700;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'JetBrains Mono', monospace;
}
.ath-id     { flex: 2; }
.ath-time   { flex: 1.5; }
.ath-type   { flex: 2; }
.ath-status { flex: 1; }
.ath-action { flex: 2; display: flex; gap: 6px; align-items: center; }

.auth-table-row {
  display: flex;
  align-items: center;
  padding: 12px 12px;
  border: 1px solid #1e293b;
  border-radius: 0 0 6px 6px;
  gap: 0;
  transition: background 0.3s;
}
.atr-pending  { background: rgba(251,191,36,0.04); }
.atr-approved { background: rgba(52,211,153,0.04); border-color: rgba(52,211,153,0.2); }

.atr-client-icon { font-size: 18px; margin-right: 8px; flex-shrink: 0; }
.atr-client-info { display: flex; flex-direction: column; gap: 1px; }
.atr-client-name { font-size: 12px; font-weight: 700; color: #94a3b8; }
.atr-client-sub  { font-size: 10px; color: #334155; font-family: 'JetBrains Mono', monospace; }

.atr-time {
  font-size: 11px;
  color: #475569;
  font-family: 'JetBrains Mono', monospace;
}

.atr-type-badge {
  font-size: 10px;
  color: #818cf8;
  background: rgba(129,140,248,0.1);
  border: 1px solid rgba(129,140,248,0.2);
  border-radius: 4px;
  padding: 2px 6px;
  font-family: 'JetBrains Mono', monospace;
}

.atr-status-pending,
.atr-status-approved {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
}
.atr-status-pending  { color: #fbbf24; }
.atr-status-approved { color: #34d399; }
.atr-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #fbbf24;
  animation: applyPulseArc 1s ease-in-out infinite;
}
.atr-dot-approved {
  background: #34d399;
  animation: none;
  box-shadow: 0 0 5px #34d399;
}

.atr-approve-time {
  font-size: 10px;
  color: #34d399;
  font-family: 'JetBrains Mono', monospace;
  margin-right: 4px;
}

/* TLS distribution success bar */
.auth-tls-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-top: 8px;
  background: rgba(52,211,153,0.06);
  border: 1px solid rgba(52,211,153,0.2);
  border-radius: 6px;
  animation: tlsSlideIn 0.4s ease;
}
@keyframes tlsSlideIn {
  from { opacity: 0; transform: translateY(-6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.tls-icon { font-size: 14px; flex-shrink: 0; }
.tls-text { flex: 1; font-size: 11px; color: #6ee7b7; line-height: 1.5; }
.tls-badge {
  font-size: 9px;
  font-weight: 700;
  color: #34d399;
  background: rgba(52,211,153,0.15);
  border: 1px solid rgba(52,211,153,0.3);
  border-radius: 3px;
  padding: 2px 6px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1px;
  flex-shrink: 0;
}

/* ── Fog node topology config module ── */
.fog-module {
  margin-top: 24px;
  background: #0a0f1a;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  overflow: hidden;
}
.fog-module-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #0d1526;
  border-bottom: 1px solid #1e3a5f;
}
.fog-module-title {
  font-size: 13px;
  font-weight: 700;
  color: #e2e8f0;
}
.fog-module-badge {
  font-size: 11px;
  color: #818cf8;
  background: rgba(129,140,248,0.1);
  border: 1px solid rgba(129,140,248,0.25);
  border-radius: 4px;
  padding: 2px 8px;
}
.fog-online-badge {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #34d399;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
.fog-online-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 6px #34d399;
  animation: fogPulse 1s ease-in-out infinite;
}
@keyframes fogPulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 6px #34d399; }
  50%       { opacity: 0.4; box-shadow: 0 0 2px #34d399; }
}

/* Slider section */
.fog-slider-section {
  padding: 14px 16px 8px;
  border-bottom: 1px solid #0f1e35;
}
.fog-level-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}
.fog-level-labels span {
  font-size: 11px;
  color: #334155;
  transition: color 0.2s, font-weight 0.2s;
}
.fog-level-labels span.fog-lv-active {
  color: #818cf8;
  font-weight: 700;
}
.fog-slider :deep(.el-slider__bar) { background: linear-gradient(90deg, #38bdf8, #818cf8); }
.fog-slider :deep(.el-slider__button) { border-color: #818cf8; background: #1e293b; }
.fog-slider :deep(.el-slider__marks-text) { color: #475569; font-size: 10px; }

/* Topology section */
.fog-topology-wrap {
  padding: 14px 16px;
}
.fog-topology-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}
.fog-topo-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
}
.fog-topo-sub {
  font-size: 11px;
  color: #334155;
}

/* Node grid */
.fog-node-grid {
  display: grid;
  grid-template-columns: repeat(var(--cols), 1fr);
  gap: 4px;
  transition: grid-template-columns 0.4s ease;
}
.fog-node-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  background: #0d1526;
  border: 1px solid #1e3a5f;
  border-radius: 4px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, transform 0.15s;
  aspect-ratio: 1;
  min-height: 0;
  overflow: hidden;
}
.fog-node-cell:hover {
  border-color: #38bdf8;
  background: rgba(56,189,248,0.07);
  transform: scale(1.06);
  z-index: 2;
}
/* Level color themes */
.fog-node-lv1 { border-color: rgba(56,189,248,0.35); }
.fog-node-lv1:hover { border-color: #38bdf8; }
.fog-node-lv2 { border-color: rgba(129,140,248,0.35); }
.fog-node-lv2:hover { border-color: #818cf8; background: rgba(129,140,248,0.07); }
.fog-node-lv3 { border-color: rgba(52,211,153,0.25); }
.fog-node-lv3:hover { border-color: #34d399; background: rgba(52,211,153,0.06); }

.fog-node-pulse {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 5px #34d399;
  flex-shrink: 0;
  animation: fogPulse 1.2s ease-in-out infinite;
}
/* Stagger pulse animations for different nodes */
.fog-node-cell:nth-child(3n)   .fog-node-pulse { animation-delay: 0.3s; }
.fog-node-cell:nth-child(5n)   .fog-node-pulse { animation-delay: 0.6s; }
.fog-node-cell:nth-child(7n)   .fog-node-pulse { animation-delay: 0.9s; }
.fog-node-cell:nth-child(11n)  .fog-node-pulse { animation-delay: 1.1s; }

.fog-node-id {
  font-size: 9px;
  font-weight: 700;
  color: #475569;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  letter-spacing: 0.5px;
  line-height: 1;
  transition: color 0.2s;
}
.fog-node-cell:hover .fog-node-id { color: #94a3b8; }
/* Too many Lv.3 nodes, reduce font size */
.fog-node-lv3 .fog-node-id { font-size: 7px; }
.fog-node-lv3 .fog-node-pulse { width: 4px; height: 4px; }

/* Tooltip content */
.fog-tooltip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: 'JetBrains Mono', monospace;
  min-width: 200px;
}
.fog-tt-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 11px;
}
.fog-tt-key { color: #64748b; flex-shrink: 0; }
.fog-tt-val { color: #cbd5e1; text-align: right; }
.fog-tt-green { color: #34d399; }

/* Dynamic stats note */
.fog-stat-note {
  margin-top: 10px;
  font-size: 11px;
  color: #475569;
  line-height: 1.7;
  padding: 8px 10px;
  background: rgba(56,189,248,0.04);
  border: 1px solid rgba(56,189,248,0.1);
  border-radius: 6px;
}
.fog-stat-hl {
  color: #38bdf8;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.fog-academic-note {
  margin: 0 16px 14px;
  font-size: 11px;
  color: #818cf8;
  background: rgba(129,140,248,0.06);
  border-left: 3px solid #818cf8;
  border-radius: 0 4px 4px 0;
  padding: 6px 10px;
  line-height: 1.6;
}

/* Slider hint text */
.fog-slider-hint {
  margin-top: 10px;
  font-size: 11px;
  color: #64748b;
  line-height: 1.7;
  padding: 7px 10px;
  background: rgba(129,140,248,0.05);
  border: 1px solid rgba(129,140,248,0.15);
  border-radius: 6px;
}

/* C1 waiting status hint */
.cn-duty-status-hint {
  font-size: 10px;
  color: #34d399;
  margin-top: 2px;
  padding-left: 11px;
  font-family: 'JetBrains Mono', monospace;
  opacity: 0.8;
  animation: hintBlink 2s ease-in-out infinite;
}
@keyframes hintBlink {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 0.3; }
}

/* ── End user authorization distribution module ── */
.auth-module {
  margin-top: 16px;
  background: #0d1117;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  overflow: hidden;
}
.auth-module-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #111827;
  border-bottom: 1px solid #1e3a5f;
}
.auth-module-title {
  font-size: 13px;
  font-weight: 700;
  color: #e2e8f0;
}
.auth-module-badge {
  font-size: 11px;
  color: #34d399;
  background: rgba(52,211,153,0.1);
  border: 1px solid rgba(52,211,153,0.25);
  border-radius: 4px;
  padding: 2px 8px;
}
/* Pending approval badge */
.auth-module-notify {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
  color: #fbbf24;
  background: rgba(251,191,36,0.1);
  border: 1px solid rgba(251,191,36,0.25);
  border-radius: 10px;
  padding: 2px 8px;
  animation: notifyPulse 1.5s ease-in-out infinite;
}
@keyframes notifyPulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(251,191,36,0.3); }
  50%      { box-shadow: 0 0 0 4px rgba(251,191,36,0); }
}
.notify-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 5px #fbbf24;
}

.auth-module-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* No request status */
.auth-empty {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  font-size: 12px;
  color: #475569;
  background: rgba(71,85,105,0.06);
  border: 1px dashed #1e293b;
  border-radius: 8px;
}
.auth-empty-icon { font-size: 18px; }

/* Received request card */
.auth-request-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  background: rgba(251,191,36,0.05);
  border: 1px solid rgba(251,191,36,0.25);
  border-radius: 10px;
  animation: requestSlideIn 0.35s ease;
}
@keyframes requestSlideIn {
  from { opacity:0; transform:translateY(-8px); }
  to   { opacity:1; transform:translateY(0); }
}
.arc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #fbbf24;
}
.arc-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 6px #fbbf24;
  flex-shrink: 0;
  animation: applyPulseArc 1s ease-in-out infinite;
}
@keyframes applyPulseArc {
  0%,100% { opacity:1; } 50% { opacity:0.3; }
}
.arc-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
  background: rgba(0,0,0,0.2);
  border-radius: 6px;
  padding: 8px 10px;
}
.arc-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  gap: 8px;
}
.arc-key { color: #64748b; flex-shrink: 0; }
.arc-val { color: #94a3b8; text-align: right; font-weight: 600; }
.arc-tip {
  font-size: 11px;
  color: #f87171;
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: 6px;
  padding: 6px 10px;
}
.arc-actions {
  display: flex;
  gap: 8px;
}

/* Approved card */
.auth-approved-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(52,211,153,0.07);
  border: 1px solid rgba(52,211,153,0.25);
  border-radius: 10px;
}
.aac-icon { font-size: 22px; flex-shrink: 0; }
.aac-text { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.aac-title { font-size: 12px; font-weight: 700; color: #34d399; }
.aac-desc  { font-size: 11px; color: #6ee7b7; }
</style> 